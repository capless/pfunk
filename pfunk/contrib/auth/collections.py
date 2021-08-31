import functools
import json
import random
import datetime

import dateutil
import jwt
from cachetools.func import ttl_cache
from cryptography.fernet import Fernet
from envs import env
from faunadb.errors import BadRequest
from werkzeug.utils import cached_property

from pfunk import StringField, Collection, Enum, EnumField
from pfunk.contrib.auth.resources import LoginUser, UpdatePassword, Public, UserRole
from pfunk.exceptions import LoginFailed
from pfunk.fields import EmailField, SlugField, ManyToManyField, ListField, ReferenceField
from pfunk.client import q


AccountStatus = Enum(name='AccountStatus', choices=['ACTIVE', 'INACTIVE'])


class Group(Collection):
    name = StringField(required=True)
    slug = SlugField(unique=True, required=False)
    users = ManyToManyField('pfunk.contrib.auth.collections.User', relation_name='users_groups')

    def __unicode__(self):
        return self.name  # pragma: no cover


class BaseUser(Collection):
    #Settings
    _credential_field = 'password'
    collection_functions = [LoginUser, UpdatePassword]
    collection_roles = [Public, UserRole]
    non_public_fields = ['groups']
    #Fields
    username = StringField(required=True, unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    account_status = EnumField(AccountStatus, required=True, default_value="INACTIVE")

    def __unicode__(self):
        return self.username  # pragma: no cover

    @classmethod
    def login(cls, username, password, _token=None):
        c = cls()
        try:
            return c.client(_token=_token).query(
                q.call("login_user", {"username": username, "password": password})
            )
        except BadRequest:
            raise LoginFailed('The login credentials you entered are incorrect.')

    @classmethod
    def get_from_id(cls, _token=None):
        c = cls()
        ref = c.client(_token=_token).query(
            q.current_identity()
        )
        return cls(_ref=ref, _lazied=True)

    @classmethod
    def update_password(cls, current_password, new_password, _token=None):
        c = cls()
        return c.client(_token=_token).query(
            q.call("update_password", {'current_password': current_password, 'new_password': new_password})
        )

    @classmethod
    def get_current_user(cls, _token=None):
        c = cls()
        return cls.get(c.client(_token=_token).query(q.current_identity()).id())

    def __unicode__(self):
        return self.username  # pragma: no cover


class UserGroups(Collection):
    collection_name = 'users_groups'
    userID = ReferenceField('pfunk.contrib.auth.collections.User')
    groupID = ReferenceField(Group)
    permissions = ListField()


class PermissionGroup(object):
    valid_actions: list = ['create', 'read', 'delete', 'write']

    def __init__(self, collection: Collection, permissions: list):
        if not issubclass(collection, Collection):
            raise ValueError('Permission class requires a Collection class as the first argument.')
        self.collection = collection
        self._permissions = permissions
        self.collection_name = self.collection.get_class_name()

    @cached_property
    def permissions(self):
        return [f'{self.collection_name}-{i}'.lower() for i in self._permissions if i in self.valid_actions]


class User(BaseUser):
    groups = ManyToManyField(Group, 'users_groups')

    @classmethod
    def get_permissions(cls, ref, _token=None):
        return cls.get(ref, _token).permissions(_token=_token)

    def get_groups(self, _token=None):
        return [Group.get(i.id(), _token=_token) for i in self.client(_token=_token).query(
            q.paginate(q.match('users_groups_by_user', self.ref))
        ).get('data')]

    def permissions(self, _token=None):
        perm_list = []
        for i in self.get_groups(_token=_token):
            ug = UserGroups.get_index('users_groups_by_group_and_user', [i.ref, self.ref], _token=_token)
            for user_group in ug:
                p = []
                if isinstance(user_group.permissions, list):
                    p = [f'{user_group.groupID.slug}-{i}' for i in user_group.permissions]
                perm_list.extend(p)
        return perm_list

    def add_permissions(self, group, permissions: list, _token=None):
        perm_list = []
        for i in permissions:
            perm_list.extend(i.permissions)

        try:
            user_group = self.client(_token=_token).query(
                q.paginate(
                    q.match(
                        q.index('users_groups_by_group_and_user'),
                        group.ref,
                        self.ref
                    )
                )
            ).get('data')[0]
        except IndexError:
            user_group = None

        ug = UserGroups(userID=self, groupID=group, permissions=perm_list)
        if user_group:
            ug.ref = user_group
        ug.save()
        return ug


class Key(Collection):
    signature_key = StringField(required=True, unique=True)
    payload_key = StringField(required=True, unique=True)
    use_crud_views = False
    @classmethod
    def create_key(cls):
        c = cls()
        if len(c.all()) >= 10:
            k = c.get_key()
            k.delete()


        return c.create(signature_key=Fernet.generate_key().decode(),
                        payload_key=Fernet.generate_key().decode())

    @classmethod
    @ttl_cache(maxsize=32, ttl=60)
    def get_keys(cls):
        return cls.all()

    @classmethod
    def get_key(cls):
        return random.choice(cls.get_keys())

    @classmethod
    def create_jwt(cls, secret_claims):
        key = cls.get_key()
        pay_f = Fernet(key.payload_key)
        gmt = dateutil.tz.gettz('GMT')
        now = datetime.datetime.now(tz=gmt)
        exp = now + datetime.timedelta(days=1)
        payload = {
            'iat': now.timestamp(),
            'exp': exp.timestamp(),
            'nbf': now.timestamp(),
            'iss': env('CORKY_ISSUER', 'corky'),
            'til': pay_f.encrypt(json.dumps(secret_claims).encode()).decode()
        }
        return jwt.encode(payload, key.signature_key, algorithm="HS256", headers={'kid': key.ref.id()}), exp

    @classmethod
    def decrypt_jwt(cls, encoded):
        headers = jwt.get_unverified_header(encoded)
        key = Key.get(headers.get('kid'))
        decoded = jwt.decode(encoded, key.signature_key, algorithms="HS256", verify=True,
                             options={"require": ["iat", "exp", "nbf", 'iss', 'til']})
        pay_f = Fernet(key.payload_key.encode())
        k = pay_f.decrypt(decoded.get('til').encode())
        return json.loads(k.decode())
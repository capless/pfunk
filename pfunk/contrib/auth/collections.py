import datetime
import json
import random
import uuid

import jwt
from cachetools.func import ttl_cache
from cryptography.fernet import Fernet
from dateutil import tz
from envs import env
from faunadb.errors import BadRequest, NotFound
from werkzeug.utils import cached_property

from pfunk.client import q
from pfunk.collection import Collection, Enum
from pfunk.contrib.auth.resources import LoginUser, UpdatePassword, Public, UserRole, LogoutUser
from pfunk.contrib.auth.views import LoginView, SignUpView, VerifyEmailView, LogoutView
from pfunk.contrib.email.base import send_email
from pfunk.exceptions import LoginFailed
from pfunk.fields import EmailField, SlugField, ManyToManyField, ListField, ReferenceField, StringField, EnumField

AccountStatus = Enum(name='AccountStatus', choices=['ACTIVE', 'INACTIVE'])


class Key(Collection):
    signature_key = StringField(required=True, unique=True)
    payload_key = StringField(required=True, unique=True)
    use_crud_views = False

    @classmethod
    def create_key(cls):
        c = cls()
        key_cnt = len(c.all())
        if key_cnt >= 10:
            over = key_cnt-10
            for i in range(over):
                k = c.get_key()
                try:
                    k.delete()
                except NotFound:
                    pass

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
        gmt = tz.gettz('GMT')
        now = datetime.datetime.now(tz=gmt)
        exp = now + datetime.timedelta(days=1)
        payload = {
            'iat': now.timestamp(),
            'exp': exp.timestamp(),
            'nbf': now.timestamp(),
            'iss': env('PROJECT_NAME', 'pfunk'),
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


class Group(Collection):
    name = StringField(required=True)
    slug = SlugField(unique=True, required=False)
    users = ManyToManyField('pfunk.contrib.auth.collections.User', relation_name='users_groups')

    def __unicode__(self):
        return self.name  # pragma: no cover


def attach_verification_key(doc):
    if not doc.ref and doc.use_email_verification:
        doc.attach_verification_key()


def send_verification_email(doc):
    doc.send_verification_email()


class BaseUser(Collection):
    # Settings
    _credential_field = 'password'
    collection_functions = [LoginUser, UpdatePassword, LogoutUser]
    collection_roles = [Public, UserRole]
    non_public_fields = ['groups']
    use_email_verification = True
    # Views
    collection_views = [LoginView, SignUpView, VerifyEmailView, LogoutView]
    # Signals
    pre_create_signals = [attach_verification_key]
    post_create_signals = [send_verification_email]
    # Fields
    username = StringField(required=True, unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    verification_key = StringField(required=False, unique=True)
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
    def logout(cls, _token=None):
        c = cls()
        return c.client(_token=_token).query(
            q.call("logout_user")
        )

    def permissions(self, _token=None):
        return []

    @classmethod
    def api_login(cls, username, password, _token=None):
        token = cls.login(username=username, password=password, _token=_token)
        print('Raw Token: ', token)
        user = cls.get_current_user(_token=token)
        claims = user.to_dict().copy()
        try:
            claims.get('data').pop('verification_key')
        except KeyError:
            pass
        claims['token'] = token
        claims['permissions'] = user.permissions()

        return Key.create_jwt(claims)

    @classmethod
    def get_from_id(cls, _token=None):
        c = cls()
        ref = c.client(_token=_token).query(
            q.current_identity()
        )
        return cls(_ref=ref, _lazied=True)

    def attach_verification_key(self):
        self.verification_key = uuid.uuid4()

    @classmethod
    def verify_email(cls, verification_key):
        user = cls.get_by('unique_User_verification_key', [verification_key])
        user.verification_key = ''
        user.account_status = 'ACTIVE'
        user.save()

    def send_verification_email(self, from_email=None):
        project_name = env('PROJECT_NAME', '')
        try:
            send_email(
                txt_template='auth/verification_email.txt',
                html_template='auth/verification_email.html',
                to_emails=[self.email],
                from_email=from_email or env('DEFAULT_FROM_EMAIL'),
                subject=f'{project_name} Email Verification',
                first_name=self.first_name,
                last_name=self.last_name,
                verification_key=self.verification_key
            )
        except:
            pass
    @classmethod
    def forgot_password(cls, email):
        pass

    @classmethod
    def signup(cls, _token=None, **kwargs):
        data = kwargs
        data['account_status'] = 'INACTIVE'
        try:
            data.pop('groups')
        except KeyError:
            pass
        cls.create(**data, _token=_token)

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

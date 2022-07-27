import datetime
import json
import random
import uuid

import jwt
from cryptography.fernet import Fernet
from dateutil import tz
from envs import env
from jwt import ExpiredSignatureError
from valley.utils import import_util
from werkzeug.utils import cached_property

from pfunk import Collection
from pfunk.exceptions import Unauthorized


class Key(object):

    @classmethod
    def create_keys(cls):
        c = cls()
        keys = {}
        for i in range(10):
            kid = str(uuid.uuid4())
            k = {'signature_key': Fernet.generate_key().decode(), 'payload_key': Fernet.generate_key().decode(),
                 'kid': kid}
            keys[kid] = k
        return keys

    @classmethod
    def import_keys(cls):
        try:
            keys = import_util(env('KEY_MODULE', 'bad.import'))
        except ImportError:
            keys = {}
        return keys

    @classmethod
    def get_keys(cls):
        keys = cls.import_keys()
        return list(keys.values())

    @classmethod
    def get_key(cls):

        return random.choice(cls.get_keys())

    @classmethod
    def create_jwt(cls, secret_claims):

        key = cls.get_key()
        pay_f = Fernet(key.get('payload_key'))
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
        return jwt.encode(payload, key.get('signature_key'), algorithm="HS256", headers={'kid': key.get('kid')}), exp

    @classmethod
    def decrypt_jwt(cls, encoded):
        headers = jwt.get_unverified_header(encoded)
        keys = cls.import_keys()
        key = keys.get(headers.get('kid'))
        try:
            decoded = jwt.decode(encoded, key.get('signature_key'), algorithms="HS256", verify=True,
                                 options={"require": ["iat", "exp", "nbf", 'iss', 'til']})
        except ExpiredSignatureError:
            raise Unauthorized('Unauthorized')
        pay_f = Fernet(key.get('payload_key').encode())
        k = pay_f.decrypt(decoded.get('til').encode())
        return json.loads(k.decode())


class PermissionGroup(object):
    """ List of permission that a user/object has

    Attributes:
        collection (`pfunk.collection.Collection`, required):
            Collection to allow permissions
        permission (list, required):
            What operations should be allowed `['create', 'read', 'delete', 'write']`
    """
    valid_actions: list = ['create', 'read', 'delete', 'write']

    def __init__(self, collection: Collection, permissions: list):
        if not issubclass(collection, Collection):
            raise ValueError(
                'Permission class requires a Collection class as the first argument.')
        self.collection = collection
        self._permissions = permissions
        self.collection_name = self.collection.get_class_name()

    @cached_property
    def permissions(self):
        """ Lists all collections and its given permissions """
        return [f'{self.collection_name}-{i}'.lower() for i in self._permissions if i in self.valid_actions]

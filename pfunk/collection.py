from envs import env
from faunadb.client import FaunaClient
from valley.schema import BaseSchema
from valley.contrib import Schema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from valley.utils import import_util

from .client import q
from valley.properties import BaseProperty, CharProperty, ListProperty


class PFunkDeclaredVars(DeclaredVars):
    base_field_class = BaseProperty


class PFunkDeclarativeVariablesMetaclass(DeclarativeVariablesMetaclass):
    declared_vars_class = PFunkDeclaredVars


class Enum(Schema):
    name = CharProperty(required=True)
    choices = ListProperty(required=True)
    
    
class Collection(BaseSchema, metaclass=PFunkDeclarativeVariablesMetaclass):
    """
    Base class for all pFunk Documents classes.
    """
    BUILTIN_DOC_ATTRS = []
    _functions = []
    _indexes = []
    _lazied = False

    def get_collection_name(self):
        return self.get_class_name().capitalize()

    def get_enums(self):
        return [i.enum for i in self._base_properties.values() if isinstance(i, import_util('pfunk.EnumField'))]

    def __getattr__(self, name):
        if name in list(self._base_properties.keys()):
            if self._lazied:
                self._get(self.ref.id())
                self._lazied = False
            prop = self._base_properties[name]
            return prop.get_python_value(self._data.get(name))

    @property
    def client(self):
        if self._token:
            return FaunaClient(secret=self._token)
        if self._client:
            return self._client
        self._client = FaunaClient(secret=env('FAUNA_SECRET'))
        return self._client

    @classmethod
    def create(cls, _credentials=None, **kwargs):
        c = cls(**kwargs)
        data_dict = {
            "data": c.get_db_valules()
        }
        if _credentials and isinstance(_credentials, dict):
            data_dict['credentials'] = _credentials
        c.validate()
        resp = c.client.query(
            q.create(
                q.collection(c.get_collection_name()),
                data_dict
            ))
        c.ref = resp['ref']
        return c

    @classmethod
    def publish_functions(cls):
        c = cls()
        for i in cls._functions:
            i(c).publish()

    @classmethod
    def publish_roles(cls):
        c = cls()
        pf_list = filter(lambda x: x.startswith('role__'), dir(cls))
        for i in pf_list:
            if hasattr(c, i) and callable(getattr(c, i)):
                c.create_or_update_role(getattr(c, i)())

    def get_db_valules(self):
        return {k:self._base_properties.get(k).get_db_value(value=v) for k,v in self._data.items()}

    def save(self):
        self.validate()
        if not self.ref:
            resp = self.client.query(
                q.create(
                    q.collection(self.get_collection_name()),
                    {
                        "data": self.get_db_valules()
                    }
                ))
            self.ref = resp['ref']
        else:
            resp = self.client.query(
                q.update(
                    self.ref,
                    {
                        "data": self.get_db_valules()
                    }
                )
            )

    def _get(self, ref):
        resp = self.client.query(q.get(q.ref(q.collection(self.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        self._data = data
        self.ref = ref
        return self

    @classmethod
    def get(cls, ref):
        c = cls()
        resp = c.client.query(q.get(q.ref(q.collection(c.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        obj = c.__class__(**data)
        obj.ref = ref
        return obj

    @classmethod
    def filter(cls, **kwargs):
        pass

    def delete(self):
        self.client.query(q.delete(self.ref))
from envs import env
from faunadb.client import FaunaClient
from valley.schema import BaseSchema
from valley.contrib import Schema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from valley.utils import import_util

from .client import q
from valley.properties import BaseProperty, CharProperty, ListProperty

from .contrib.generic import GenericCreate, GenericDelete, GenericUpdate


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
    _roles = []
    _lazied = False
    _all_index = True
    _use_crud_functions = True
    _crud_functions = [GenericCreate, GenericDelete, GenericUpdate]
    _non_public_fields = []

    def __init__(self, _ref=None, _lazied=False, **kwargs):
        super(Collection, self).__init__(**kwargs)
        if _ref:
            self.ref = _ref
        self._lazied = _lazied

    def get_fields(self):
        return {k: q.select(k, q.var("input")) for k,v in self._base_properties.items() if k not in self._non_public_fields}

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

    @classmethod
    def _verbose_plural_name(cls):
        return f"{cls.get_class_name()}s"

    def all_index_name(self):
        return f"all_{self._verbose_plural_name()}"

    def call_function(self, func_name, _validate=False, **kwargs):
        if _validate:
            self._data.update(kwargs)
            self.validate()
        return self.client.query(
            q.call(func_name, kwargs)
        )

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
        c.save(_credentials=_credentials)
        return c

    @classmethod
    def publish(cls):
        cls.publish_functions()
        print(f'Published {cls.get_class_name()} functions successfully!')
        cls.publish_roles()
        print(f'Published {cls.get_class_name()} roles successfully!')
        cls.publish_indexes()
        print(f'Published {cls.get_class_name()} indexes successfully!')

    @classmethod
    def publish_functions(cls):
        c = cls()
        if c._use_crud_functions:
            c._functions.extend(c._crud_functions)
        for i in c._functions:
            i(c).publish()

    @classmethod
    def publish_roles(cls):
        c = cls()
        for i in cls._roles:
            i(c).publish()

    @classmethod
    def publish_indexes(cls):
        c = cls()
        for i in cls._indexes:
            i(c).publish()

    def get_db_values(self):
        data = dict()
        relational_data = dict()
        for k, v in self._data.items():
            prop = self._base_properties.get(k)
            if not prop.relation_field:
                data[k] = prop.get_db_value(value=v)
            else:
                relational_data[prop.relation_name] = v
        return data, relational_data

    def _save_related(self, relational_data):
        for k, v in relational_data.items():
            for i in v:
                resp = self.client.query(
                    q.create(
                        q.collection(k),
                        {
                           "data": {
                               f"{self.get_class_name()}ID": self.ref,
                               f"{i.get_class_name()}ID": i.ref
                           }
                        }
                    )
                )

    def save(self, _credentials=None):
        self.validate()
        data, relational_data = self.get_db_values()
        data_dict = dict()
        data_dict['data'] = data
        if _credentials:
            data_dict['credentials'] = _credentials
        if not self.ref:
            resp = self.client.query(
                q.create(
                    q.collection(self.get_collection_name()),
                    data_dict
                ))
            self.ref = resp['ref']
        else:
            self.client.query(
                q.update(
                    self.ref,
                    data_dict
                )
            )
        self._save_related(relational_data)

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

    def process_qs(self, data):
        return [self.__class__(_ref=i, _lazied=True) for i in data]

    @classmethod
    def all(cls, paginate_by=100, after=None, before=None):
        c = cls()
        raw_qs = c.client.query(q.paginate(q.match(q.index(c.all_index_name())), paginate_by, after=after, before=before))
        return c.process_qs(raw_qs.get('data'))


    @classmethod
    def filter(cls, **kwargs):
        pass

    def delete(self):
        self.client.query(q.delete(self.ref))
from envs import env
from faunadb.client import FaunaClient
from faunadb.errors import BadRequest
from valley.schema import BaseSchema
from valley.contrib import Schema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from valley.utils import import_util

from .client import q
from valley.properties import BaseProperty, CharProperty, ListProperty

from .contrib.generic import GenericCreate, GenericDelete, GenericUpdate, AllFunction
from .resources import Index


class PFunkDeclaredVars(DeclaredVars):
    base_field_class = BaseProperty


class PFunkDeclarativeVariablesMetaclass(DeclarativeVariablesMetaclass):
    declared_vars_class = PFunkDeclaredVars


class Enum(Schema):
    name = CharProperty(required=True)
    choices = ListProperty(required=True)

    def __unicode__(self):
        return self.name
    
    
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
    _crud_functions = [GenericCreate, GenericDelete, GenericUpdate, AllFunction]
    _non_public_fields = []
    _verbose_plural_name = None

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
    def get_verbose_plural_name(cls):
        if cls._verbose_plural_name:
            return cls._verbose_plural_name
        return f"{cls.get_class_name()}s"

    def all_index_name(self):
        return f"all_{self.get_verbose_plural_name()}"

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

    def get_unique_together(self):
        try:
            meta_unique_together = self.Meta.unique_together
        except AttributeError:
            return
        unique_together = []

        for i in meta_unique_together:
            fields = '_'.join(i)
            name = f'{self.get_class_name()}_unique_{fields}'
            terms = [{'binding': f, 'field': ['data', f]} for f in i]
            unique = True
            source = self.get_collection_name()
            Indy = type(''.join([f.capitalize() for f in i])+'Index', (Index, ), {
                'name': name,
                'terms': terms,
                'unique': unique,
                'source': source
            })
            unique_together.append(Indy)
        return unique_together



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
        ut = c.get_unique_together()
        if ut:
            cls._indexes.extend(ut)
        for i in cls._indexes:
            try:
                i().publish(c.client)
            except BadRequest as e:
                for err in e.errors:
                    print(f'Error ({i.__name__.lower()}): ', err.description)

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

    @classmethod
    def get_by(cls, name, *args):
        c = cls()
        raw_qs = c.client.query(
            q.paginate(q.match(q.index(name), *args)))
        return c.process_qs(raw_qs.get('data'))[0]

    def process_qs(self, data):
        return [self.__class__(_ref=i, _lazied=True) for i in data]

    @classmethod
    def all(cls, paginate_by=100, after=None, ts=None):
        c = cls()
        return [cls(_ref=i.get('ref'), **i.get('data')) for i in c.call_function(
            c.all_index_name(), size=paginate_by, after=after, ts=ts).get('data')]

    @classmethod
    def get_index(cls, index_name, page_size=100):
        c = cls()
        return [cls(_ref=i.get('ref'), **i.get('data')) for i in c.client.query(
            q.map_(
                q.lambda_(['ref'],
                          q.get(q.var('ref'))
                          ),
                q.paginate(
                    q.match(q.index(index_name)),
                    page_size
                )
            )
        ).get('data')]

    @classmethod
    def filter(cls, **kwargs):
        pass

    def delete(self):
        self.client.query(q.delete(self.ref))
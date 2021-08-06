from envs import env
from .client import FaunaClient
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
        return self.name  # pragma: no cover


class Collection(BaseSchema, metaclass=PFunkDeclarativeVariablesMetaclass):
    """
    Base class for all pFunk Collection classes.
    """
    BUILTIN_DOC_ATTRS = []
    _functions = []
    _indexes = []
    _roles = []
    _lazied = False
    _all_index = True
    _use_crud_functions = False
    _crud_functions = [GenericCreate, GenericDelete, GenericUpdate, AllFunction]
    _non_public_fields = []
    _verbose_plural_name = None
    _collection_name = None

    def __init__(self, _ref=None, _lazied=False, **kwargs):
        super(Collection, self).__init__(**kwargs)
        if _ref:
            self.ref = _ref
        self._lazied = _lazied

    def get_fields(self):
        return {k: q.select(k, q.var("input")) for k,v in self._base_properties.items() if k not in self._non_public_fields}

    def get_collection_name(self):
        return self._collection_name or self.get_class_name().capitalize()

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

    def all_function_name(self):
        return f"all_{self.get_verbose_plural_name()}_function"

    def call_function(self, func_name, _validate=False, _token=None, **kwargs):
        if _validate:
            self._data.update(kwargs)
            self.validate()
        return self.client(_token=_token).query(
            q.call(func_name, kwargs)
        )

    def client(self, _token=None):
        if _token:
            return FaunaClient(secret=_token)
        return FaunaClient(secret=env('FAUNA_SECRET'))

    @classmethod
    def create(cls, _credentials=None, _token=None, **kwargs):
        c = cls(**kwargs)
        c.save(_credentials=_credentials, _token=_token)
        return c

    ##############
    # Deployment #
    ##############
    @classmethod
    def publish(cls):
        cls.publish_functions()

        test_mode = env('PFUNK_TEST_MODE', False, var_type='boolean')
        if not test_mode:
            print(f'Published {cls.get_class_name()} functions successfully!')  #pragma: no cover
        cls.publish_indexes()
        if not test_mode:
            print(f'Published {cls.get_class_name()} indexes successfully!') #pragma: no cover
        cls.publish_roles()
        if not test_mode:
            print(f'Published {cls.get_class_name()} roles successfully!') #pragma: no cover

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
                i().publish(c.client())
            except BadRequest as e:
                for err in e.errors:
                    print(f'Error ({i.__name__.lower()}): ', err.description)

    @classmethod
    def unpublish(cls):
        c = cls()
        print(f'Unpublishing: {c.get_collection_name()}')
        result = c.client().query(
            q.delete(q.collection(c.get_collection_name()))
        )
        return result

    def get_unique_together(self):
        try:
            meta_unique_together = self.Meta.unique_together
        except AttributeError:
            return []
        unique_together = set()

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
            unique_together.add(Indy)
        return list(unique_together)

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

    def _save_related(self, relational_data, _token=None):
        client = self.client(_token=_token)
        for k, v in relational_data.items():
            for i in v:
                try:
                    resp = client.query(
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
                except BadRequest:
                    pass

    def save(self, _credentials=None, _token=None):
        self.validate()
        data, relational_data = self.get_db_values()

        data_dict = dict()
        data_dict['data'] = data

        if _credentials:
            data_dict['credentials'] = {
                'password': _credentials
            }

        if not self.ref:
            resp = self.client(_token=_token).query(
                q.create(
                    q.collection(self.get_collection_name()),
                    data_dict
                ))
            self.ref = resp['ref']
        else:
            self.client(_token=_token).query(
                q.update(
                    self.ref,
                    data_dict
                )
            )
        self._save_related(relational_data, _token=_token)

    def _get(self, ref, _token=None):
        resp = self.client(_token=_token).query(q.get(q.ref(q.collection(self.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        self._data = data
        self.ref = ref
        return self

    @classmethod
    def get(cls, ref, _token=None):
        c = cls()
        resp = c.client(_token=_token).query(q.get(q.ref(q.collection(c.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']

        obj = c.__class__(**data)
        obj.ref = ref
        return obj

    @classmethod
    def get_by(cls, name, *args, _token=None):
        c = cls()
        raw_qs = c.client(_token=_token).query(
            q.paginate(q.match(q.index(name), *args)))
        return c.process_qs(raw_qs.get('data'))[0]

    def process_qs(self, data):
        return [self.__class__(_ref=i, _lazied=True) for i in data]

    @classmethod
    def all(cls, page_size=100, after=None, before=None, ts=None, events=False, sources=False, _token=None):
        return cls.get_index(cls().all_index_name(), page_size=page_size, after=after, before=before, ts=ts, events=events,
                       sources=sources, _token=_token)

    @classmethod
    def get_index(cls, index_name, terms=[], page_size=100, after=None, before=None, ts=None, events=False,
                  sources=False, _token=None):
        c = cls()
        return [cls(_ref=i.get('ref'), **i.get('data')) for i in c.client(_token=_token).query(
            q.map_(
                q.lambda_(['ref'],
                          q.get(q.var('ref'))
                          ),
                q.paginate(
                    q.match(q.index(index_name), terms),
                    size=page_size,
                    after=after,
                    before=before,
                    ts=ts,
                    events=events
                )
            )
        ).get('data')]

    def delete(self, _token=None):
        self.client(_token=_token).query(q.delete(self.ref))

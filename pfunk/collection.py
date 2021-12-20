from envs import env
from faunadb.errors import BadRequest
from valley.contrib import Schema
from valley.declarative import DeclaredVars, DeclarativeVariablesMetaclass
from valley.properties import BaseProperty, CharProperty, ListProperty
from valley.schema import BaseSchema
from valley.utils import import_util

from pfunk.client import FaunaClient
from pfunk.web.views.json import DetailView, CreateView, UpdateView, DeleteView, ListView
from .client import q
from .contrib.generic import GenericCreate, GenericDelete, GenericUpdate, AllFunction
from .exceptions import DocNotFound
from .queryset import Queryset
from .resources import Index

__all__ = ['Enum', 'Collection']


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
    Base class for all pFunk Collection classes. In Fauna, a Collection is analogous to a table in Postgresql or MySQL.
    This class is analogous to a model in Django.
    """
    BUILTIN_DOC_ATTRS: list = []
    collection_functions: list = []
    """Functions that are attached to this collection."""
    collection_indexes: list = []
    """Indexes that are attached to this collection."""
    collection_roles: list = []
    """Roles that are attached to this collection."""
    all_index: bool = True
    """Specifies whether to create the all index."""
    use_crud_functions: bool = False
    """Specifies whether to create the CRUD functions"""
    crud_functions: list = [GenericCreate, GenericDelete, GenericUpdate, AllFunction]
    """Specifies the CRUD functions used if the `use_crud_functions` variable is `True`"""
    use_crud_views: bool = True
    """Specifies whether to use the CRUD views."""
    crud_views: list = [CreateView, UpdateView, ListView, DeleteView, DetailView]
    """Specifies the base events used if the `use_base_events` variable is `True`"""
    require_auth: bool = True
    """Determines wheter to require authentication and authorization"""
    non_public_fields: list = []
    """Specifies all fields that are not public."""
    verbose_plural_name: str = None
    """Overrides the default plural collection name."""
    collection_name: str = None
    """Overrides the default collection name."""
    collection_views: list = []
    """Events that are attached to this collection."""
    protected_vars: list = ['functions', 'indexes', 'roles', 'lazied', 'all_index', 'use_crud_functions',
                            'use_base_events', 'base_events', 'non_public_fields', 'verbose_plural_name',
                            'collection_name']
    """List of class variables that are not allowed a field names. """

    def __init__(self, _ref: object = None, _lazied: bool = False, **kwargs) -> None:
        """
        Args:
            _ref: Fauna ref instance (faunadb.objects.Ref)
            _lazied: Specifies if the full document is supplied at instance initialization. If this is True we will
            get the full document at the first evaluation.
            **kwargs: keyword arguments to build the document attributes.
        """

        super(Collection, self).__init__(**kwargs)
        intersected_var_names = set(self.protected_vars).intersection(self._base_properties.keys())
        if len(intersected_var_names) != 0:
            raise ValueError(f'You are using protected var names in your schema: {intersected_var_names}')

        if _ref:
            self.ref = _ref
        self._lazied = _lazied
        self.collection_indexes = set(self.collection_indexes)
        self.collection_roles = set(self.collection_roles)
        self.collection_functions = set(self.collection_functions)
        if self.use_crud_views:
            self.collection_views.extend(self.crud_views)
        self.collection_views = set(self.collection_views)

        if self.use_crud_functions:
            for i in self.crud_functions:
                self.collection_functions.add(i)

    def get_fields(self) -> dict:
        """
        Helper method that helps to build the body for the generic functions.

        Returns: dict

        """
        return {k: q.select(k, q.var("input")) for k, v in self._base_properties.items() if
                k not in self.non_public_fields}

    def get_collection_name(self) -> str:
        """
        Returns the capitalized name of the collection.

        Returns: str

        """
        return self.collection_name or self.get_class_name().capitalize()

    def get_enums(self) -> list:
        """
        Returns a list of Enums based on the EnumFields. This is helpful when building the GraphQL schema template.

        Returns: list

        """
        return [i.enum for i in self._base_properties.values() if isinstance(i, import_util('pfunk.EnumField'))]

    def __getattr__(self, name):
        if name in list(self._base_properties.keys()):
            if self._lazied:
                self._get(self.ref.id())
                self._lazied = False
            prop = self._base_properties[name]
            return prop.get_python_value(self._data.get(name))

    @classmethod
    def get_verbose_plural_name(cls) -> str:
        """
        Returns a plural name for the collection. You can supply the verbose plural name of your choice by using the

        Returns: str

        """

        if cls.verbose_plural_name:
            return cls.verbose_plural_name
        return f"{cls.get_class_name()}s"

    def all_index_name(self) -> str:
        """
        Returns the name of the "all" index used in the .all() method.

        Returns: str

        """

        return f"all_{self.get_verbose_plural_name()}"

    def all_function_name(self) -> str:
        """
        Returns the name of the "all" generic function.

        Returns: str

        """

        return f"all_{self.get_verbose_plural_name()}_function"

    def call_function(self, func_name: str, _validate: bool = False, _token: str = None, **kwargs):
        """
        Call a Fauna user defined function (UDF).
        Args:
            func_name: Name of the function
            _validate: If True the keyword arguments will validated against Collection schema
            _token: Token (secret) used to make call
            **kwargs: keyword arguments

        Returns: dict

        """

        if _validate:
            self._data.update(kwargs)
            self.validate()
        return self.client(_token=_token).query(
            q.call(func_name, kwargs)
        )

    def client(self, _token=None) -> FaunaClient:
        """
        Initializes FaunaClient
        Args:
            _token: Token (secret) used to initialize client

        Returns: FaunaClient

        """

        if _token:
            return FaunaClient(secret=_token)
        return FaunaClient(secret=env('FAUNA_SECRET'))

    @classmethod
    def create(cls, _credentials=None, _token=None, **kwargs):
        """
        Create a new document
        Args:
            _credentials: If this Collection provides authentication this would be the password field.
            _token: Token (secret) used to make call
            **kwargs: Keyword arguments used to specify the document's attributes

        Returns: Collection

        """

        c = cls(**kwargs)
        c.save(_credentials=_credentials, _token=_token)
        return c

    ##############
    # Deployment #
    ##############
    @classmethod
    def publish(cls) -> None:
        """
        Publish the collection to Fauna

        Returns: None
        """
        cls.publish_functions()

        test_mode = env('PFUNK_TEST_MODE', False, var_type='boolean')
        if not test_mode:
            print(f'Published {cls.get_class_name()} functions successfully!')  # pragma: no cover
        cls.publish_indexes()
        if not test_mode:
            print(f'Published {cls.get_class_name()} indexes successfully!')  # pragma: no cover
        cls.publish_roles()
        if not test_mode:
            print(f'Published {cls.get_class_name()} roles successfully!')  # pragma: no cover

    @classmethod
    def publish_functions(cls) -> None:
        """
        Publish functions specified in the collection to Fauna.

        Returns: None
        """
        c = cls()
        if c.use_crud_functions:
            for f in c.crud_functions:
                c.collection_functions.add(f)
        for i in c.collection_functions:
            i(c).publish()

    @classmethod
    def publish_roles(cls) -> None:
        """
        Publish roles specified in the collection to Fauna

        Returns: None
        """
        c = cls()
        for i in cls.collection_roles:
            i(c).publish()

    @classmethod
    def publish_indexes(cls) -> None:
        """
        Publish indexes specified in the collection to Fauna

        Returns: None
        """
        c = cls()
        c.get_unique_together()

        for i in cls.collection_indexes:
            try:
                i().publish(c.client())
            except BadRequest as e:
                for err in e.errors:
                    print(f'Error ({i.__name__.lower()}): ', err.description)

    @classmethod
    def unpublish(cls) -> None:
        """
        Delete the collection

        Returns: None
        """
        c = cls()
        print(f'Unpublishing: {c.get_collection_name()}')
        result = c.client().query(
            q.delete(q.collection(c.get_collection_name()))
        )
        return result

    def get_unique_together(self) -> None:
        """
        Builds Indexes based on the self.Meta.unique_together attribute

        Returns: None
        """
        try:
            meta_unique_together = self.Meta.unique_together
        except AttributeError:
            return None

        for i in meta_unique_together:
            fields = '_'.join(i)
            name = f'{self.get_class_name()}_unique_{fields}'
            terms = [{'binding': f, 'field': ['data', f]} for f in i]
            unique = True
            source = self.get_collection_name()

            Indy = type(self.get_collection_name().capitalize() + ''.join([f.capitalize() for f in i]) + 'Index',
                        (Index,), {
                            'name': name,
                            'terms': terms,
                            'unique': unique,
                            'source': source
                        })
            self.collection_indexes.add(Indy)

    def get_db_values(self) -> tuple:
        """
        Get and transform the values before sending to the database.

        Returns: tuple
        """
        data = dict()
        relational_data = dict()
        for k, v in self._data.items():
            prop = self._base_properties.get(k)
            if not prop.relation_field:
                data[k] = prop.get_db_value(value=v)
            else:
                relational_data[prop.relation_name] = v
        return data, relational_data

    def get_foreign_fields_by_type(self, cls_str):
        cls = import_util(cls_str)
        return {k: {'foreign_class': v.foreign_class, 'field_type': v.__class__.__name__} for k, v in
                self._base_properties.items() if isinstance(v, cls)}

    def _save_related(self, relational_data, _token=None) -> None:
        """
        Save related data
        Args:
            relational_data: dict that contains data to be saved
            _token: Token (secret) used to make call

        Returns: None

        """

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

    def call_signals(self, name):
        signals = getattr(self, name) or []
        for i in signals:
            i(self)

    def get_data_dict(self, _credentials=None):
        data, relational_data = self.get_db_values()

        data_dict = dict()
        data_dict['data'] = data

        if _credentials:
            data_dict['credentials'] = {
                'password': _credentials
            }
        return data_dict, relational_data

    def save(self, _credentials=None, _token=None) -> None:
        """
        Save current instance to Fauna
        Args:
            _credentials: If this Collection provides authentication this would be the password field.
            _token: Token (secret) used to make call

        Returns: None

        """
        self.call_signals('pre_validate_signals')
        self.validate()

        if not self.ref:
            self.call_signals('pre_create_signals')
            data_dict, relational_data = self.get_data_dict(_credentials=_credentials)
            resp = self.client(_token=_token).query(
                q.create(
                    q.collection(self.get_collection_name()),
                    data_dict
                ))
            self.ref = resp['ref']
            self.call_signals('post_create_signals')
        else:
            data_dict, relational_data = self.get_data_dict(_credentials=_credentials)
            self.call_signals('pre_update_signals')
            self.client(_token=_token).query(
                q.update(
                    self.ref,
                    data_dict
                )
            )

        self.call_signals('pre_save_related_signals')
        self._save_related(relational_data, _token=_token)
        self.call_signals('post_save_signals')

    def _get(self, ref, _token=None):
        """
        Instance method to get one document by ref
        Args:
            ref: Ref (ID) string
            _token: Token (secret) used to make call

        Returns: Collection

        """

        resp = self.client(_token=_token).query(q.get(q.ref(q.collection(self.get_collection_name()), ref)))
        ref = resp['ref']
        data = resp['data']
        self._data = self.process_schema_kwargs(data)
        self.ref = ref
        return self

    @classmethod
    def get(cls, ref, _token=None):
        """
        Class method to get one document by ref
        Args:
            ref: Ref (ID) string
            _token: Token (secret) used to make call

        Returns: Collection

        """
        return cls()._get(ref, _token=_token)

    @classmethod
    def all(cls, page_size=100, after=None, before=None, ts=None, events=False, sources=False, _token=None) -> list:
        """
        Calls the built-in "all" index.
        Args:
            page_size: The number of records to paginate by.
            after: Optional - Return the next Page of results after this cursor (inclusive).
            before: Optional - Return the previous Page of results before this cursor (exclusive).
            ts: Optional - default current. Return the results at the specified point in time (number of UNIX microseconds or a Timestamp).
            events: Optional - default False. If True, return a Page from the event history of the input.
            sources: Optional - default false. If true, includes the source of truth providing why this object was included in the results.
            _token: Token (secret) used to make call

        Returns: list

        """

        return cls.get_index(cls().all_index_name(), page_size=page_size, after=after, before=before, ts=ts,
                             events=events,
                             sources=sources, _token=_token)

    @classmethod
    def get_by(cls, index_name, terms=[], use_map=True):
        try:
            return cls.get_index(index_name, terms=terms, use_map=use_map)[0]
        except IndexError:
            raise DocNotFound('Document not found.')

    @classmethod
    def get_index(cls, index_name, terms=[], page_size=100, after=None, before=None, ts=None, events=False,
                  sources=False, use_map=True, _token=None):
        """
        Call an index
        Args:
            index_name: Name of the index
            terms: Fields that should be indexed together.
            page_size: The number of records to paginate by.
            after: Optional - Return the next Page of results after this cursor (inclusive).
            before: Optional - Return the previous Page of results before this cursor (exclusive).
            ts: Optional - default current. Return the results at the specified point in time (number of UNIX microseconds or a Timestamp).
            events: Optional - default False. If True, return a Page from the event history of the input.
            sources: Optional - default false. If true, includes the source of truth providing why this object was included in the results.
            _token: Token (secret) used to make call

        Returns:

        """

        c = cls()
        if use_map:
            query_response = c.client(_token=_token).query(
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
            )
            lazied = False
        else:
            query_response = c.client(_token=_token).query(
                q.paginate(
                    q.match(q.index(index_name), terms),
                    size=page_size,
                    after=after,
                    before=before,
                    ts=ts,
                    events=events
                )
            )
            lazied = True

        return Queryset(query_response, cls, lazied)

    def delete(self, _token=None) -> None:
        """
        Delete document
        Args:
            _token: Token (secret) used to make call

        Returns: None

        """
        self.call_signals('pre_delete_signals')
        self.client(_token=_token).query(q.delete(self.ref))
        self.call_signals('post_delete_signals')

    @classmethod
    def delete_from_id(cls, id: str, _token=None) -> None:
        c = cls()
        c.call_signals('pre_delete_signals')
        c.client(_token=_token).query(q.delete(q.ref(q.collection(c.get_collection_name()), id)))
        c.call_signals('post_delete_signals')

    ########
    # JSON #
    ########

    def to_dict(self):
        field_data = self._data.copy()
        ref = {'id': self.ref.id(), 'collection': self.ref.collection().id()}
        obj = {
            'ref': ref,
            'data': field_data
        }
        return obj

    #######
    # API #
    #######

    @property
    def urls(self):
        """
        Returns list of URLs
        Returns: list

        """
        return [i.url(self) for i in self.collection_views]

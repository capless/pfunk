import logging
import requests
from envs import env
from io import BytesIO
from faunadb.errors import BadRequest
from valley.contrib import Schema
from valley.properties import CharProperty, BooleanProperty, ForeignProperty, ForeignListProperty
from .loading import client, q
from .collection import Collection, Enum, Index
from .template import graphql_template

logger = logging.getLogger('pfunk')


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class TermValueField(Schema):
    name = CharProperty(required=True)
    reverse = BooleanProperty(default_value=True)


class Binding(Schema):
    name = CharProperty(required=True)


class TermValue(Schema):
    bindings = ForeignListProperty(Binding, required=False)
    fields = ForeignListProperty(TermValueField, required=False)

    def render(self):
        obj_list = []
        if self.bindings:
            binding_list = [{"binding": i.name} for i in self.bindings]
            obj_list.extend(binding_list)
        if self.fields:
            field_list = [{'field': ['data', i.name], 'reverse': i.reverse} for i in self.fields]
            obj_list.extend(field_list)
        return obj_list


class Index(Schema):
    name = CharProperty(required=True)
    source = CharProperty(required=True)
    terms = ForeignProperty(TermValue, required=False)
    values = ForeignProperty(TermValue, required=False)
    serialized = BooleanProperty(default_value=True)
    unique = BooleanProperty(default_value=False)

    def render(self):
        pass

    def get_kwargs(self):
        self.validate()
        kwargs = {'name': self.name, 'source': q.collection(self.source), 'serialized': self.serialized,
                  'unique': self.unique}
        if self.terms:
            kwargs['terms'] = self.terms.render()
        if self.values:
            kwargs['values'] = self.values.render()
        return kwargs

    def publish(self):
        return client.query(q.create_index(self.get_kwargs()))


class Database(Schema):
    name = CharProperty(required=True)
    _collection_list = []
    _enum_list = []
    _index_list = []

    def add_resource(self, resource):
        if not issubclass(resource, (Collection, Enum, Index)):
            raise ValueError('Resource has to be one of the following: Collection, Enum, or Index')
        if issubclass(resource, Collection) and resource not in self._collection_list:
            self._collection_list.append(resource)
            cl = set(self._collection_list)
            self._collection_list = list(cl)

    def render(self):
        return graphql_template.render(collection_list=self._collection_list, enum_list=self._enum_list,
                                       index_list=self._index_list)

    def get_meta(self):
        default = {
            'all_index': True,
            'all_index_name': self.get_class_name()
        }
        return default

    def publish(self, override: bool = False):
        gql_io = BytesIO(self.render().encode())
        mode = 'update'
        if override:
            mode = 'override'
        resp = requests.post(
            'https://graphql.fauna.com/import',
            params={'mode': mode},
            auth=BearerAuth(env('FAUNA_SECRET')),
            data=gql_io
        )

        return resp.content

    def create(self):
        self.validate()
        if self._is_valid:
            try:
                client.query(q.create_database({"name": self.name}))
            except BadRequest:
                logger.warning(f'{self.name} database already exists.')

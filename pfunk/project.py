import logging

import requests
from io import BytesIO

from envs import env
from faunadb.client import FaunaClient
from jinja2 import Template
from valley.contrib import Schema

from valley.properties import CharProperty, ForeignProperty

from .resources import Index
from .client import q
from .collection import Collection, Enum
from .template import graphql_template

logger = logging.getLogger('pfunk')


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class Project(Schema):
    name = CharProperty(required=True)
    client = ForeignProperty(FaunaClient)

    _collection_list = []
    _enum_list = []
    _index_list = []
    _role_list = []
    extra_graphql = None

    def add_resource(self, resource):
        if isinstance(resource, Enum):
            resource_list = self._enum_list
        elif issubclass(resource, Collection):
            resource_list = self._collection_list
        elif issubclass(resource, Index):
            resource_list = self._index_list
        else:
            raise ValueError(
                'Resource has to be one of the following: Collection, Enum, or Index')
        if not resource in resource_list:
            resource_list.append(resource)

    def add_resources(self, resource_list):
        for i in resource_list:
            self.add_resource(i)

    def add_enums(self):
        for i in self._collection_list:
            enums = i().get_enums()
            for e in enums:
                self.add_resource(e)

    def get_extra_graphql(self):
        if self.extra_graphql:
            return Template(self.extra_graphql).render(**self.get_extra_graphql_context())
        return ''

    def get_extra_graphql_context(self):
        return {'env': env}

    def render(self):
        self.add_enums()
        return graphql_template.render(collection_list=self._collection_list, enum_list=self._enum_list,
                                       index_list=self._index_list, function_list=self._func,
                                       extra_graphql=self.get_extra_graphql())

    @property
    def _client(self):
        if self.client:
            return self.client
        self.client = FaunaClient(secret=env('FAUNA_SECRET'))
        return self.client

    def publish(self, mode='merge'):
        gql_io = BytesIO(self.render().encode())
        if self.client:
            secret = self.client.secret
        else:
            secret = env('FAUNA_SECRET')
        resp = requests.post(
            env('FAUNA_GRAPHQL_URL', 'https://graphql.fauna.com/import'),
            params={'mode': mode},
            auth=BearerAuth(secret),
            data=gql_io
        )
        for ind in set(self._index_list):
            ind().publish(self._client)
        for col in set(self._collection_list):
            col.publish()
        return resp.content

    def unpublish(self):
        for ind in set(self._index_list):
            ind().unpublish(self._client)
        for col in set(self._collection_list):
            col.unpublish_collection()

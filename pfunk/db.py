import logging
from collections import OrderedDict

import requests
from io import BytesIO

from envs import env
from faunadb.client import FaunaClient
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


class Database(Schema):
    name = CharProperty(required=True)
    client = ForeignProperty(FaunaClient)

    _collection_list = []
    _enum_list = []
    _index_list = []
    _role_list = []

    def add_resource(self, resource):
        if isinstance(resource, Enum):
            resource_list = self._enum_list
        elif issubclass(resource, Collection):
            resource_list = self._collection_list
        elif issubclass(resource, Index):
            resource_list = self._index_list
        else:
            raise ValueError('Resource has to be one of the following: Collection, Enum, or Index')
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

    def render(self):
        self.add_enums()
        return graphql_template.render(collection_list=self._collection_list, enum_list=self._enum_list,
                                       index_list=self._index_list)

    def publish(self, mode='merge'):
        gql_io = BytesIO(self.render().encode())
        if self.client:
            secret = self.client.secret
        else:
            secret = env('FAUNA_SECRET')
        resp = requests.post(
            'https://graphql.fauna.com/import',
            params={'mode': mode},
            auth=BearerAuth(secret),
            data=gql_io
        )
        for i in self._collection_list:
            i.publish()
        return resp.content

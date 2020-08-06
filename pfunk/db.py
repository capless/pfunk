import logging
import requests
from envs import env
from io import BytesIO
from faunadb.errors import BadRequest
from valley.contrib import Schema

from valley.properties import CharProperty

from .indexes import Index
from .loading import client, q
from .collection import Collection
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
    _collection_list = []
    _enum_list = []
    _index_list = []

    def add_resource(self, resource):
        if not issubclass(resource, (Collection, Index)):
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

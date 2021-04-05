import logging
import requests
from envs import env
from io import BytesIO
from faunadb.errors import BadRequest
from valley.contrib import Schema

from valley.properties import CharProperty

from .indexes import Index
from .loading import super_client, q
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
    _collection_list = []
    _enum_list = []
    _index_list = []

    def add_resource(self, resource):
        if issubclass(resource, Collection):
            resource_list = self._collection_list
        elif issubclass(resource, Enum):
            resource_list = self._enum_list
        elif issubclass(resource, Index):
            resource_list = self._index_list
        else:
            print(resource)
            raise ValueError('Resource has to be one of the following: Collection, Enum, or Index')
        if resource not in resource_list:
            resource_list.append(resource)



    def render(self):
        return graphql_template.render(collection_list=self._collection_list, enum_list=self._enum_list,
                                       index_list=self._index_list)

    def get_meta(self):
        default = {
            'all_index': True,
            'all_index_name': self.get_class_name()
        }
        return default

    def publish(self, mode='merge'):
        gql_io = BytesIO(self.render().encode())
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
                super_client.query(q.create_database({"name": self.name}))
            except BadRequest:
                logger.warning(f'{self.name} database already exists.')

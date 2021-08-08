import logging

import requests
from io import BytesIO

from envs import env
from faunadb.client import FaunaClient
from jinja2 import Template
from valley.contrib import Schema

from valley.properties import CharProperty, ForeignProperty

from .collection import Collection
from .template import graphql_template

logger = logging.getLogger('pfunk')

__all__ = ['Project']

class BearerAuth(requests.auth.AuthBase):
    """
    Bearer Token Auth class for the requests library.
    """
    def __init__(self, token):
        """

        Args:
            token: Fauna secret token
        """
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class Project(Schema):
    """
    Project configuration class.
    """
    name: str = CharProperty(required=True)
    client: FaunaClient = ForeignProperty(FaunaClient)


    extra_graphql: str = None

    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        self.collections = set()
        self.enums = set()
        self.indexes = set()
        self.functions = set()

    def add_resource(self, resource) -> None:
        """
        Add collection to the project
        Args:
            resource: Collection class

        Returns: None

        """

        if issubclass(resource, Collection):
            self.collections.add(resource)
        else:
            raise ValueError(
                'Resource has to be one of the following: Collection')

    def add_resources(self, resource_list) -> None:
        """
        Add multiple collections to the project.
        Args:
            resource_list: list of collection classes

        Returns: None

        """

        for i in resource_list:
            self.add_resource(i)

    def get_enums(self) -> set:
        """
        Get all of the Enums added to the project.

        Returns: set

        """

        for i in self.collections:
            enums = i().get_enums()
            for e in enums:
                self.enums.add(e)
        return self.enums

    def get_extra_graphql(self) -> str:
        """
        Get the rendered "Extra GraphQL" template

        Returns: str
        """
        if self.extra_graphql:
            return Template(self.extra_graphql).render(**self.get_extra_graphql_context())
        return ''

    def get_extra_graphql_context(self) -> dict:
        """
        Returns a dict of context variables to be used when rendering the "Extra GraphQL"

        Returns: dict
        """
        return {'env': env}

    def render(self) -> str:
        """
        Renders the GraphQL template before it is sent to Fauna

        Returns: str
        """
        self.get_enums()
        return graphql_template.render(collection_list=self.collections, enum_list=self.enums,
                                       index_list=self.indexes, function_list=self._func,
                                       extra_graphql=self.get_extra_graphql())

    def publish(self, mode:str='merge') -> int:
        """
        Publishes the collections, indexes, functions, and roles to Fauna
        Args:
            mode: Import mode. The choices are merge, replace, and override.

        Returns: int

        """

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
        if resp.status_code == 200:
            test_mode = env('PFUNK_TEST_MODE', False, var_type='boolean')
            if not test_mode:
                print('GraphQL Schema Imported Successfully!!') #pragma: no cover
        for col in set(self.collections):
            col.publish()
        return resp.status_code

    def unpublish(self) -> None:
        """
        Unpublish collections, indexes, and functions

        Returns: None
        """
        for ind in self.indexes:
            ind().unpublish(self._client)
        for col in self.collections:
            col.unpublish()

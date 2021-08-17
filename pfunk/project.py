import logging
from functools import lru_cache

import requests
from io import BytesIO

from envs import env

from faunadb.client import FaunaClient
from jinja2 import Template
from valley.contrib import Schema

from valley.properties import CharProperty, ForeignProperty, ForeignListProperty
from valley.utils import import_util
from werkzeug.routing import Map
from werkzeug.utils import cached_property
from .api.events import Event
from .api.http import HTTPRequest, RESTRequest
from .collection import Collection
from .fields import ForeignList
from .template import graphql_template

logger = logging.getLogger('pfunk')

__all__ = ['Project']


API_EVENT_TYPES = {
        'aws:api-rest': ['resource', 'path', 'httpMethod', 'headers',
                         'multiValueHeaders', 'queryStringParameters',
                         'multiValueQueryStringParameters',
                         'pathParameters', 'stageVariables',
                         'requestContext', 'body', 'isBase64Encoded'
                         ],
        'aws:api-http': [
            'version', 'routeKey', 'rawPath', 'rawQueryString',
            'headers', 'requestContext', 'isBase64Encoded'
        ]
    }


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
    name: str = CharProperty(required=False)
    client: FaunaClient = ForeignProperty(FaunaClient, required=False)
    _collections: list = ForeignList(Collection, required=False)

    extra_graphql: str = None

    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        self.validate()
        self.collections = set(self._collections or [])
        self.event_types = set()
        self.enums = set()
        self.indexes = set()
        self.functions = set()

    def add_event_type(self, event_type):
        """
        Add event type to the project
        Args:
            event_type: Event

        Returns:

        """
        if issubclass(event_type, Event):
            self.event_types.add(event_type)
        elif issubclass(event_type, str):
            try:
                et = import_util(event_type)
            except ImportError:
                et = None
            if issubclass(et, Event):
                self.event_types.add(et)
        else:
            raise ValueError('Event Type has to be one of the following: Event')

    def add_resource(self, resource) -> None:
        """
        Add collection to the project
        Args:
            resource: Collection class

        Returns: None

        """

        if issubclass(resource, Collection):
            self.collections.add(resource)
        elif issubclass(resource, str):
            try:
                r = import_util(resource)
            except ImportError:
                r = None
            if issubclass(r, Collection):
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

    def event_handler(self, event: dict, context: object) -> object:
        event_type = self.get_event_type(event)
        if event_type in ['aws:api-http', 'aws:api-rest']:
            if event_type == 'aws:api-http':
                request = HTTPRequest(event)
            elif event_type == 'aws:api-rest':
                request = RESTRequest(event)
            view, kwargs = self.urls.match(request.path, request.method)
            return view(event, context, kwargs)
        return self.get_event(self.get_event_object(event), context)

    def get_event_type(self, event: dict) -> str:
        """
        Determine the event type (ex. REST API, HTTP API, SQS, S3, SNS, SES)
        Args:
            event: Event dictionary

        Returns: str

        """
        event_keys = event.keys()

        if 'Records' in event_keys:
            event = event['Records'][0]
            return event.get('EventSource') or event.get('eventSource')

        for k, v in API_EVENT_TYPES.items():
            matched = len(set(v).intersection(event_keys)) >= len(v)
            if matched:
                return k

    @cached_property
    def urls(self):
        rules = []
        for i in self.collections:
            col = i()
            rules.extend(col.urls)
        _map = Map(
            rules=rules,
            strict_slashes=True
        )
        return _map.bind('')






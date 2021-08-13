import json

from werkzeug.routing import Rule
from pfunk.api.http import Request, RESTRequest, HTTPRequest


class View(object):
    url_prefix: str
    """Specifies a prefix to use in the get_url method."""
    request_class: Request = Request

    def __init__(self, collection):
        self.collection = collection
        self.request: Request

    @property
    def urls(self):
        raise NotImplementedError

    def get_request(self, event):
        raise NotImplementedError

    def get_response(self, event, context):
        self.get_request(event)
        response = self.process_request()

        return response.to_dict()

    def process_request(self):
        response = getattr(self, self.request.method)()
        return response

    def get_request(self, event):
        self.request = self.request_class(event)




class RESTEvent(View):
    request_class = RESTRequest
    event_keys: list = ['resource', 'path', 'httpMethod', 'headers',
                        'multiValueHeaders', 'queryStringParameters',
                        'multiValueQueryStringParameters',
                        'pathParameters', 'stageVariables',
                        'requestContext', 'body', 'isBase64Encoded'
                        ]


class HTTPEvent(View):
    request_class = HTTPRequest
    event_keys: list = [
        'version', 'routeKey', 'rawPath', 'rawQueryString',
        'cookies', 'headers', 'requestContext', 'isBase64Encoded'
    ]


class ActionMixin(object):
    action: str

    @property
    def urls(self):
        return [Rule(f'{self.collection}/{self.action}/')]


class IDMixin(ActionMixin):

    @property
    def urls(self):
        return [Rule(f'{self.collection}/<int:id>/{self.action}/')]


class CreateEvent(ActionMixin, HTTPEvent):
    action = 'create'


class UpdateEvent(IDMixin, HTTPEvent):
    action = 'update'


class DetailEvent(IDMixin, HTTPEvent):
    action = 'detail'


class DeleteEvent(IDMixin, HTTPEvent):
    action = 'delete'


class ListEvent(ActionMixin):
    action = 'list'

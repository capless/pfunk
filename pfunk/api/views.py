from werkzeug.routing import Rule
from pfunk.api.http import Request, RESTRequest, HTTPRequest


class View(object):
    url_prefix: str
    """Specifies a prefix to use in the get_url method."""
    request_class: Request = Request
    http_methods: list = ['get']

    def __init__(self, collection):
        self.collection = collection
        self.request: Request
        self.context: object

    @property
    def url(self):
        raise NotImplementedError

    def get_request(self, event, kwargs):
        self.request = self.request_class(event, kwargs)

    def get_response(self, event, context, kwargs):

        self.get_request(event, kwargs)
        self.lambda_context = context

        response = self.process_request(context=self.get_context())
        return response.response

    def get_context(self):
        return {}

    def process_request(self):
        response = getattr(self, self.request.method)()
        return response

    def get_request(self, event):
        self.request = self.request_class(event)


class RESTView(View):
    request_class = RESTRequest
    event_keys: list = ['resource', 'path', 'httpMethod', 'headers',
                        'multiValueHeaders', 'queryStringParameters',
                        'multiValueQueryStringParameters',
                        'pathParameters', 'stageVariables',
                        'requestContext', 'body', 'isBase64Encoded'
                        ]


class HTTPView(View):
    request_class = HTTPRequest
    event_keys: list = [
        'version', 'routeKey', 'rawPath', 'rawQueryString',
        'cookies', 'headers', 'requestContext', 'isBase64Encoded'
    ]


class ActionMixin(object):
    action: str

    @property
    def url(self):
        return [Rule(f'{self.collection}/{self.action}/', endpoint=self.as_view(), methods=[self.http_method])]


class IDMixin(ActionMixin):

    @property
    def url(self):
        return [Rule(f'{self.collection}/<int:id>/{self.action}/', endpoint=self.as_view, methods=[self.http_method])]


class CreateEvent(ActionMixin, HTTPView):
    action = 'create'


class UpdateEvent(IDMixin, HTTPView):
    action = 'update'


class DetailEvent(IDMixin, HTTPView):
    action = 'detail'


class DeleteEvent(IDMixin, HTTPView):
    action = 'delete'


class ListEvent(ActionMixin, HTTPView):
    action = 'list'

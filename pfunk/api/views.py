from faunadb.errors import NotFound, PermissionDenied
from werkzeug.routing import Rule
from pfunk.api.http import Request, RESTRequest, HTTPRequest, JSONResponse, HttpNotFoundResponse, HttpForbiddenResponse
from pfunk.exceptions import TokenValidationFailed


class View(object):
    url_prefix: str
    """Specifies a prefix to use in the get_url method."""
    request_class: Request = Request
    http_methods: list = ['get']

    def __init__(self, collection, auth_required=True):
        self.collection = collection
        self.request: Request
        self.context: object

    @classmethod
    def url(cls, collection):
        raise NotImplementedError

    def get_response(self, request, context, kwargs):
        self.request = request
        self.lambda_context = context

        response = self.process_response_middleware(self.process_request())

        return response.response

    def process_response_middleware(self, response):
        return response

    def get_context(self):
        return {}

    def process_request(self):
        try:
            response = getattr(self, self.request.method.lower())()
        except NotFound:
            return HttpNotFoundResponse(
                content={
                    'success': False,
                    'msg': 'Not Found'
                }
            )
        except (PermissionDenied, TokenValidationFailed):
            return HttpForbiddenResponse(
                content={
                    'success': False,
                    'msg': 'Permission denied'
                }
            )

        return response

    @classmethod
    def as_view(cls, collection):
        c = cls(collection)

        def view(request, context, kwargs):
            return c.get_response(request, context, kwargs)
        return view


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

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/{cls.action}/', endpoint=cls.as_view(collection), methods=cls.http_methods)


class IDMixin(ActionMixin):

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/<int:id>/{cls.action}/', endpoint=cls.as_view(collection),
                    methods=cls.http_methods)


class CreateView(ActionMixin, HTTPView):
    action = 'create'
    http_methods = ['post']


class UpdateView(IDMixin, HTTPView):
    action = 'update'


class DetailView(IDMixin, HTTPView):
    action = 'detail'

    def get(self, **kwargs):
        try:
            return JSONResponse(
                content={
                    'success': True,
                    'data': self.collection.get(self.request.kwargs.get('id'))
                }
            )
        except NotFound:
            return HttpNotFoundResponse(
                content={
                    'success': False,
                    'msg': 'Not Found'
                }
            )
    

class DeleteView(IDMixin, HTTPView):
    action = 'delete'

    def delete(self, **kwargs):
        return JSONResponse(
            content={
                'success': True,
                'data': self.collection.delete_from_id(self.request.kwargs.get('id'))
            }
        )


class ListView(ActionMixin, HTTPView):
    action = 'list'

    def get(self, **kwargs):
        return JSONResponse(
            content={
                'success': True,
                'data': self.collection.all()
            }
        )



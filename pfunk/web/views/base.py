from envs import env
from faunadb.errors import NotFound as FaunaNotFound, PermissionDenied, BadRequest
from jwt import InvalidSignatureError
from valley.exceptions import ValidationException
from werkzeug.exceptions import NotFound, MethodNotAllowed
from werkzeug.http import dump_cookie
from werkzeug.routing import Rule

from pfunk.exceptions import TokenValidationFailed, LoginFailed, Unauthorized, DocNotFound, GraphQLError
from pfunk.web.request import Request, RESTRequest, HTTPRequest
from pfunk.web.response import (Response, HttpNotFoundResponse, HttpForbiddenResponse, HttpBadRequestResponse,
                                HttpMethodNotAllowedResponse, HttpUnauthorizedResponse)


class View(object):
    url_prefix: str
    """Specifies a prefix to use in the get_url method."""
    request_class: Request = Request
    response_class: Response
    not_found_class: HttpNotFoundResponse = HttpNotFoundResponse
    forbidden_class: HttpForbiddenResponse = HttpForbiddenResponse
    bad_request_class: HttpBadRequestResponse = HttpBadRequestResponse
    method_not_allowed_class: HttpMethodNotAllowedResponse = HttpMethodNotAllowedResponse
    unauthorized_class: HttpUnauthorizedResponse = HttpUnauthorizedResponse
    login_required = True
    http_methods: list = ['get']
    content_type_accepted: str
    restrict_content_type: bool = False
    action: str = ''

    def __init__(self, collection=None):
        self.collection = collection
        self.request: Request
        self.context: object
        self.headers = {}
        self.cookies = {}

    @classmethod
    def url(cls, collection):
        raise NotImplementedError

    def get_response_class(self) -> Response:
        """
        Returns the Response class
        Returns: Response
        """
        if not isinstance(self.request, Request):
            return Response
        return self.response_class

    def process(self, request, context, kwargs):

        self.request = request

        if self.restrict_content_type:
            if request.headers.get('content-type') != self.content_type_accepted:
                return self.bad_request_class('Wrong content-type')
        self.lambda_context = context

        response = self.process_request()

        return response

    def get_context(self):
        return {}

    def process_lambda_request(self):

        try:
            if self.login_required:
                self.token_check()
            response = getattr(self, self.request.method.lower())().response
        except (FaunaNotFound, NotFound, DocNotFound):
            response = self.not_found_class().response
        except PermissionDenied:
            response = self.forbidden_class().response
        except (BadRequest, GraphQLError) as e:
            response = self.bad_request_class(payload=str(e)).response
        except (ValidationException,) as e:
            key, value = str(e).split(':')
            response = self.bad_request_class(payload={'validation_errors': {key: value}}).response
        except (MethodNotAllowed,):
            response = self.method_not_allowed_class().response
        except (LoginFailed,) as e:
            response = self.unauthorized_class(payload=str(e)).response
        except (Unauthorized, InvalidSignatureError, TokenValidationFailed):
            response = self.unauthorized_class().response

        return response

    def process_wsgi_request(self):
        try:
            if self.login_required:
                self.token_check()
            response = getattr(self, self.request.method.lower())()
        except (FaunaNotFound, NotFound, DocNotFound):
            response = self.not_found_class()
        except PermissionDenied:
            response = self.forbidden_class()
        except (BadRequest, GraphQLError) as e:
            response = self.bad_request_class(payload=str(e))
        except (ValidationException,) as e:
            key, value = str(e).split(':')
            response = self.bad_request_class(payload={'validation_errors': {key: value}})
        except (MethodNotAllowed,):
            response = self.method_not_allowed_class()
        except (LoginFailed,) as e:
            response = self.unauthorized_class(payload=str(e))
        except (Unauthorized, InvalidSignatureError, TokenValidationFailed):
            response = self.unauthorized_class()
        return response

    def process_request(self):

        if isinstance(self.request, (HTTPRequest, RESTRequest)):
            return self.process_lambda_request()
        return self.process_wsgi_request()

    def get_token(self):
        from pfunk.contrib.auth.collections import Key
        enc_token = self.request.cookies.get(env('TOKEN_COOKIE_NAME', 'tk'))

        if not enc_token:
            enc_token = self.request.headers.get('Authorization', None)
        if not enc_token:
            return
        token = Key.decrypt_jwt(enc_token)
        return token

    def token_check(self):
        if self.login_required:
            token = self.get_token()
            if token:
                self.request.jwt = token
                self.request.token = token.get('token')
            else:
                raise Unauthorized

    @classmethod
    def as_view(cls, collection=None):
        c = cls(collection)

        def view(request, context, kwargs):
            return c.process(request, context, kwargs)

        return view

    def get_response(self):
        return self.get_response_class()(
            payload='',
            headers=self.get_headers()
        )

    def set_cookie(self, key: str, value: str = "",
                   max_age: int = None,
                   expires: int = None,
                   path: str = "/",
                   domain: str = None,
                   secure: bool = True,
                   httponly: bool = True,
                   charset: str = "utf-8",
                   sync_expires: bool = True,
                   max_size: int = 4093,
                   samesite: str = None):
        debug = env('DEBUG', True, var_type='boolean')
        if debug:
            secure = False
        self.cookies[key] = dump_cookie(key, value=value, max_age=max_age, expires=expires, path=path, domain=domain,
                                        secure=secure, httponly=httponly, charset=charset, sync_expires=sync_expires,
                                        max_size=max_size, samesite=samesite)

    def get_headers(self):
        if len(self.cookies.keys()) > 0:
            cookie_list = []
            for k, v in self.cookies.items():
                cookie_list.append(v)
            self.headers['Set-Cookie'] = ','.join(cookie_list)
        return self.headers

    def get_query(self):
        raise NotImplementedError

    def get_query_kwargs(self):
        raise NotImplementedError

    def put(self, **kwargs):
        return self.get_response()

    def get(self, **kwargs):
        return self.get_response()

    def post(self, **kwargs):
        return self.get_response()

    def head(self, **kwargs):
        return self.get_response()

    def delete(self, **kwargs):
        return self.get_response()


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


class QuerysetMixin(object):

    def get_query(self):
        return self.collection.all(**self.get_query_kwargs())

    def get_query_kwargs(self):
        query_kwargs = self.request.query_params
        kwargs = {
            'after': query_kwargs.get('after'),
            'before': query_kwargs.get('before')
        }
        if self.request.query_params.get('page_size'):
            kwargs['page_size'] = query_kwargs.get('page_size')
        kwargs['_token'] = self.request.token
        return kwargs


class ObjectMixin(object):

    def get_query(self):
        return self.collection.get(self.request.kwargs.get('id'), **self.get_query_kwargs())

    def get_query_kwargs(self):
        return {'_token': self.request.token}


class UpdateMixin(object):

    def get_query_kwargs(self):

        data = self.request.get_json()
        fields = self.collection.get_foreign_fields_by_type('pfunk.fields.ReferenceField')
        for k, v in fields.items():
            current_value = data.get(k)
            col = v.get('foreign_class')
            if current_value:
                obj = col.get(current_value)
                data[k] = obj

        return data


class ActionMixin(object):
    action: str

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/{cls.action}/', endpoint=cls.as_view(collection),
                    methods=cls.http_methods)


class IDMixin(ActionMixin):

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/{cls.action}/<int:id>/', endpoint=cls.as_view(collection),
                    methods=cls.http_methods)

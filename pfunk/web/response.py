import json

from pfunk.utils.json_utils import PFunkEncoder


class Response(object):
    status_code = 200
    content_type: str = 'text/html'
    default_payload: str = ''

    def __init__(self, payload=None, headers={}, *args, **kwargs):
        self.raw_payload = payload or self.default_payload
        self.raw_headers = headers

    @property
    def body(self):
        return self.raw_payload

    @property
    def headers(self):
        headers = {'Content-Type': self.content_type}
        headers.update(self.raw_headers)

        return headers

    @property
    def wsgi_headers(self):
        return self.headers.items()

    @property
    def response(self):
        return {
            'statusCode': self.status_code,
            'body': self.body,
            'headers': self.headers
    }


class NotFoundResponseMixin(object):
    status_code = 404
    default_payload = 'Not Found'
    success: bool = False


class BadRequestResponseMixin(object):
    status_code = 400
    default_payload = 'Bad Request'
    success: bool = False


class ForbiddenResponseMixin(object):
    status_code = 403
    default_payload = 'Forbidden'
    success: bool = False


class MethodNotAllowedResponseMixin(object):
    status_code = 405
    default_payload = 'Method Not Allowed'
    success: bool = False


class UnauthorizedResponseMixin(object):
    status_code = 401
    default_payload = 'Unauthorized'
    success: bool = False


class JSONResponse(Response):
    content_type: str = 'application/json'
    success: bool = True

    @property
    def body(self):
        return json.dumps({
            'success': self.success,
            'data': self.raw_payload
        }, cls=PFunkEncoder)


class GraphQLResponse(JSONResponse):

    @property
    def body(self):
        return json.dumps(self.raw_payload, cls=PFunkEncoder)


class JSONUnauthorizedResponse(UnauthorizedResponseMixin, JSONResponse):
    pass


class HttpUnauthorizedResponse(UnauthorizedResponseMixin, Response):
    pass


class JSONNotFoundResponse(NotFoundResponseMixin, JSONResponse):
    pass


class HttpNotFoundResponse(NotFoundResponseMixin, Response):
    pass


class JSONForbiddenResponse(ForbiddenResponseMixin, JSONResponse):
    pass


class HttpForbiddenResponse(ForbiddenResponseMixin, Response):
    pass


class HttpMethodNotAllowedResponse(MethodNotAllowedResponseMixin, Response):
    pass


class JSONMethodNotAllowedResponse(MethodNotAllowedResponseMixin, JSONResponse):
    pass


class HttpBadRequestResponse(BadRequestResponseMixin, Response):
    pass


class JSONBadRequestResponse(BadRequestResponseMixin, JSONResponse):
    pass
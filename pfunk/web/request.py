import json

from werkzeug.http import parse_cookie


class Request(object):
    """ Base Request object for views
    
    Attributes:
        event (str, required):
            The event key to execute  
        kwargs (optional):
            additional keyword arguments
    """

    def __init__(self, event, kwargs):
        self.raw_event = event
        self.kwargs = kwargs

        self.user = None
        self.token: str = None
        self.jwt: str = None
        
    def get_cookies(self, raw_cookies):
        return raw_cookies

    def get_json(self):
        if self.headers.get('content-type') == 'application/json':
            return json.loads(self.body)


class BaseAPIGatewayRequest(Request):

    def __init__(self, event, kwargs=None):
        super(BaseAPIGatewayRequest, self).__init__(event, kwargs)
        self.is_base64_encoded = event.get('isBase64Encoded')
        self.body = event.get('body')
        self.headers = event.get('headers', {})
        self.query_params = event.get('queryStringParameters')


class WSGIRequest(Request):

    def __init__(self, event, kwargs=None):
        super(WSGIRequest, self).__init__(event, kwargs=kwargs)
        self.method = event.method
        self.query_params = event.args
        self.body = event.data
        self.headers = event.headers
        self.path = event.path
        self.cookies = event.cookies
        self.source_ip = event.remote_addr


class RESTRequest(BaseAPIGatewayRequest):

    def __init__(self, event, kwargs=None):
        super(RESTRequest, self).__init__(event, kwargs=kwargs)
        self.resource = event['resource']
        self.method = event['httpMethod']
        self.path_params = event['pathParameters']

        try:
            self.cookies = self.get_cookies(self.headers.pop('Cookie'))
        except KeyError:
            self.cookies = {}

        self.stage_vars = event['stageVariables']
        self.path = event['path']
        self.source_ip = event.get('requestContext').get('identity').get('sourceIp')

    def get_cookies(self, raw_cookies):
        return parse_cookie(raw_cookies)


class HTTPRequest(BaseAPIGatewayRequest):

    def __init__(self, event, kwargs=None):
        super(HTTPRequest, self).__init__(event, kwargs=kwargs)
        self.raw_event = event
        self.version = event.get('version')
        self.route_key = event.get('routeKey')
        self.raw_path = event.get('rawPath')
        self.raw_query_string = event.get('rawQueryString')

        self.cookies = self.get_cookies(event.get('cookies', []))
        http = event.get('requestContext').get('web', {})
        self.method = http.get('method')
        self.path = http.get('path')
        self.source_ip = http.get('sourceIp')

    def get_cookies(self, raw_cookies):
        return parse_cookie(';'.join(raw_cookies))


# TODO: Convert this to pfunk-style oauth2 request
class OAuth2Request(BaseAPIGatewayRequest):
    def __init__(self, method, uri, body=None, headers=None):
        InsecureTransportError.check(uri)
        #: HTTP method
        self.method = method
        self.uri = uri
        self.body = body
        #: HTTP headers
        self.headers = headers or {}

        self.query = urlparse.urlparse(uri).query

        self.args = dict(url_decode(self.query))
        self.form = self.body or {}

        #: dict of query and body params
        data = {}
        data.update(self.args)
        data.update(self.form)
        self.data = data

        #: authenticate method
        self.auth_method = None
        #: authenticated user on this request
        self.user = None
        #: authorization_code or token model instance
        self.credential = None
        #: client which sending this request
        self.client = None

    @property
    def client_id(self):
        """The authorization server issues the registered client a client
        identifier -- a unique string representing the registration
        information provided by the client. The value is extracted from
        request.

        :return: string
        """
        return self.data.get('client_id')

    @property
    def response_type(self):
        return self.data.get('response_type')

    @property
    def grant_type(self):
        return self.data.get('grant_type')

    @property
    def redirect_uri(self):
        return self.data.get('redirect_uri')

    @property
    def scope(self):
        return self.data.get('scope')

    @property
    def state(self):
        return self.data.get('state')
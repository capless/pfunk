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
        """
        Returns dict of cookies
        Args:
            raw_cookies:

        Returns: dict

        """
        return raw_cookies

    def get_json(self):
        """
        Get JSON response body
        Returns: dict

        """
        if self.headers.get('content-type') == 'application/json':
            return json.loads(self.body)


class BaseAPIGatewayRequest(Request):
    """
    Base API Gateway Request
    """

    def __init__(self, event, kwargs=None):
        super(BaseAPIGatewayRequest, self).__init__(event, kwargs)
        self.is_base64_encoded = event.get('isBase64Encoded')
        self.body = event.get('body')
        self.headers = event.get('headers', {})
        self.query_params = event.get('queryStringParameters')


class WSGIRequest(Request):
    """
    WSGI Request
    """
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
    """
    REST Request: For REST API Gateway
    """

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
    """
    HTTP Request: For HTTP API Gateway
    """
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



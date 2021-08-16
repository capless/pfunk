import json

from pfunk.utils.json_utils import PFunkEncoder


class Request(object):

    def __init__(self, event, kwargs):
        self.raw_event = event
        self.kwargs = kwargs
        self.is_base64_encoded = event['isBase64Encoded']
        self.body = event.get('body')
        self.headers = event.get('headers', {})
        
    def get_cookies(self, raw_cookies):
        return raw_cookies


class RESTRequest(Request):

    def __init__(self, event, kwargs=None):
        super(RESTRequest, self).__init__(event, kwargs=kwargs)
        self.resource = event['resource']
        self.method = event['httpMethod']
        self.path_params = event['pathParameters']

        self.cookies = self.get_cookies(self.headers.pop('cookie'))
        self.stage_vars = event['stageVariables']
        self.path = event['path']

        self.query_string_params = event['queryStringParameters']


class HTTPRequest(Request):

    def __init__(self, event, kwargs=None):
        super(HTTPRequest, self).__init__(event, kwargs=kwargs)
        self.raw_event = event
        self.version = event.get('version')
        self.route_key = event.get('routeKey')
        self.raw_path = event.get('rawPath')
        self.raw_query_string = event.get('rawQueryString')

        self.cookies = self.get_cookies(event.get('cookies'))
        http = event.get('requestContext').get('http', {})
        self.method = http.get('method')
        self.path = http.get('path')
        self.query_string_params = event.get('queryStringParameters', {})
        self.source_ip = http.get('sourceIp')


class Response(object):
    status_code = 200

    def __init__(self, content=b'', headers={}, *args, **kwargs):
        self.raw_content = content
        self.raw_headers = headers

    @property
    def body(self):
        return self.raw_content

    @property
    def headers(self):
        return self.raw_headers

    @property
    def response(self):
        return {
            'statusCode': self.status_code,
            'body': self.body,
            'headers': self.headers
    }


class JSONResponse(Response):

    @property
    def body(self):
        return json.dumps(self.raw_content, cls=PFunkEncoder)


class HttpNotFoundResponse(Response):
    status_code = 404


class HttpForbiddenResponse(Response):
    status_code = 403


class HttpMethodNotAllowedResponse(Response):
    status_code = 405

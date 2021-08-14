import json


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
        super(RESTRequest, self).__init__(event)
        self.resource = event['resource']
        self.method = event['httpMethod']
        self.path_params = event['pathParameters']

        self.cookies = self.get_cookies(self.headers.pop('cookie'))
        self.stage_vars = event['stageVariables']
        self.path = event['path']

        self.query_string_params = event['queryStringParameters']


class HTTPRequest(Request):

    def __init__(self, event, kwargs=None):
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
        return json.load(self.raw_content)


class HttpNotFoundResponse(Response):
    status_code = 404


class HttpForbiddenResponse(Response):
    status_code = 403


class HttpMethodNotAllowedResponse(Response):
    status_code = 405


# {
# 	'version': '2.0',
# 	'routeKey': 'ANY /http-api-gateway',
# 	'rawPath': '/http-api-gateway',
# 	'rawQueryString': '',
#     'queryStringParameters': {
#             'bass': 'True',
#             'cas': 'False'
#         }
#   'cookies': ['ca=dafdsfasdfadsfafsdfadsfdasaf', 'cb=retetterterterertertetertererter'],
# 	'headers': {
# 		'accept': '*/*',
# 		'accept-encoding': 'gzip, deflate, br',
# 		'content-length': '4',
# 		'content-type': 'text/plain',
# 		'host': '66fm7ju9b8.execute-api.us-east-1.amazonaws.com',
# 		'postman-token': '58845f4e-066c-471a-80b3-26d4c28650b8',
# 		'user-agent': 'PostmanRuntime/7.28.3',
# 		'x-amzn-trace-id': 'Root=1-6116a867-3afdf5102ce6eb5b79c6532e',
# 		'x-forwarded-for': '99.140.245.215',
# 		'x-forwarded-port': '443',
# 		'x-forwarded-proto': 'https'
# 	},
# 	'requestContext': {
# 		'accountId': '986625141461',
# 		'apiId': '66fm7ju9b8',
# 		'domainName': '66fm7ju9b8.execute-api.us-east-1.amazonaws.com',
# 		'domainPrefix': '66fm7ju9b8',
# 		'http': {
# 			'method': 'PUT',
# 			'path': '/http-api-gateway',
# 			'protocol': 'HTTP/1.1',
# 			'sourceIp': '99.140.245.215',
# 			'userAgent': 'PostmanRuntime/7.28.3'
# 		},
# 		'requestId': 'EA9AJgj2oAMEMcQ=',
# 		'routeKey': 'ANY /http-api-gateway',
# 		'stage': '$default',
# 		'time': '13/Aug/2021:17:14:15 +0000',
# 		'timeEpoch': 1628874855166
# 	},
# 	'body': 'Test',
# 	'isBase64Encoded': False
# }
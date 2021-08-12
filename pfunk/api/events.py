class Event(object):
    event_keys: list


class RESTEvent(Event):
    event_keys: list = ['resource', 'path', 'httpMethod', 'headers',
                            'multiValueHeaders', 'queryStringParameters',
                            'multiValueQueryStringParameters',
                            'pathParameters', 'stageVariables',
                            'requestContext', 'body', 'isBase64Encoded'
                            ]


class HTTPEvent(Event):
    event_keys: list = [
            'version', 'routeKey', 'rawPath', 'rawQueryString',
            'cookies', 'headers', 'requestContext', 'isBase64Encoded'
        ]


class S3Event(Event):
    pass


class SQSEvent(Event):
    event_keys: list = ['Records']


class CreateEvent(HTTPEvent):
    pass


class UpdateEvent(HTTPEvent):
    pass


class DetailEvent(HTTPEvent):
    pass


class DeleteEvent(HTTPEvent):
    pass


class ListEvent(HTTPEvent):
    pass
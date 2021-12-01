import time
import json


def now_timestamp():
    return int(time.time())


def create_oauth_request(request, request_cls, use_json=False):
    if isinstance(request, request_cls):
        return request

    if request.method == 'POST':
        if use_json:
            body = json.loads(request.body)
        else:
            body = request.POST.dict()
    else:
        body = None

    url = request.build_absolute_uri()
    return request_cls(request.method, url, body, request.headers)

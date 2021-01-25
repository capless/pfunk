from pfunk.loading import FaunaClient
from faunadb import query as q


def create_function_from_kwargs(client: FaunaClient = None, **kwargs: dict):
    _create_function(client, kwargs)


def create_function_from_dict(client: FaunaClient = None, data: dict = {}):
    _create_function(client, data)


def _create_function(client: FaunaClient = None, data: dict = {}):
    if not client and not isinstance(client, FaunaClient):
        raise ValueError("client is Null OR Not FaunaClient")

    response = client.query(q.create_function(data))
    return response

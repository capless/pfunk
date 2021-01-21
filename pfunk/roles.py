from pfunk.loading import FaunaClient
from faunadb import query as q


def create_role_from_kwargs(client: FaunaClient = None, **kwargs: dict):
    _create_role(client, kwargs)


def create_role_from_dict(client: FaunaClient = None, data: dict = {}):
    _create_role(client, data)


def _create_role(client: FaunaClient = None, data: dict = {}):
    if not client and not isinstance(client, FaunaClient):
        raise ValueError("client is Null OR Not FaunaClient")

    reqs = ['name', 'privileges', 'membership']
    for req in reqs:
        data[req]
        
    response = client.query(q.create_role(data))
    return response

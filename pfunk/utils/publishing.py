import requests
from faunadb import query as q
from faunadb.errors import BadRequest


class BearerAuth(requests.auth.AuthBase):
    """
    Bearer Token Auth class for the requests library.
    """
    def __init__(self, token):
        """

        Args:
            token: Fauna secret token
        """
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

def create_or_update_role(client, payload:dict={}):
    """
    Utility that attempts to create a role and if that fails it attempts to update it.
    Args:
        client: FaunaClient instance
        payload: dict containing the details about the role

    Returns: query

    """
    try:
        response = client.query(
            q.create_role(payload)
        )
    except BadRequest as err:

        payload_copy = payload.copy()
        role_name = payload_copy.pop("name")

        response = client.query(
            q.update(
                q.role(role_name),
                payload_copy
            )
        )

    return response


def create_or_pass_index(client, payload):
    """
    Utility that attempts to create a index and if that fails it attempts to update it.
    Args:
        client: FaunaClient instance
        payload: dict containing the details about the index

    Returns: query

    """
    try:
        response = client.query(
            q.create_index(payload)
        )
    except BadRequest as err:
        print('Warning: You cannot update an index please delete the index and publish it again.')
        print(err)
        return

    return response


def create_or_update_function(client, payload):
    """
    Utility that attempts to create a function and if that fails it attempts to update it.
    Args:
        client: FaunaClient instance
        payload: dict contains the details about the function

    Returns: query

    """
    try:
        response = client.query(
            q.create_function(
                payload
            )
        )
    except BadRequest as e:
        payload_copy = payload.copy()
        function_name = payload_copy.pop('name')
        response = client.query(
            q.update(
                q.function(function_name),
                payload_copy
            )
        )

    return response
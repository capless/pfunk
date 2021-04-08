from faunadb import query as q
from faunadb.errors import BadRequest


def create_or_update_role(client, payload={}):
    try:
        response = client.query(
            q.create_role(payload)
        )
    except BadRequest as err:

        if str(err) == 'Role already exists.':
            role_name = payload.pop("name")
            response = client.query(
                q.update(
                    q.role(role_name),
                    payload
                )
            )
        else:
            raise err
    return response


def create_or_update_function(client, payload):
    try:
        response = client.query(
            q.create_function(
                payload
            )
        )
    except BadRequest as e:
        if e._get_description() == 'Function already exists.':
            function_name = payload.pop('name')
            response = client.query(
                q.update(
                    q.function(function_name),
                    payload
                )
            )
        else:
            raise e
    return response
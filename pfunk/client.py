from envs import env
from faunadb.client import FaunaClient as FC
from faunadb import query as q
from faunadb.objects import Ref


class FaunaClient(FC):

    def __init__(
            self,
            secret=None,
            domain="db.fauna.com",
            scheme="https",
            port=None,
            timeout=60,
            observer=None,
            pool_connections=10,
            pool_maxsize=10,
            **kwargs):
        self.secret = secret or env('FAUNA_SECRET')
        if not self.secret:
            raise ValueError('When creating a FaunaClient instance you must supply the secret argument or set the '
                             'FAUNA_SECRET environment variable.')

        super(FaunaClient, self).__init__(secret,
            domain=domain,
            scheme=scheme,
            port=port,
            timeout=timeout,
            observer=observer,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            **kwargs)
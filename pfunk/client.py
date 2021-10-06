from envs import env
from faunadb.client import FaunaClient as FC
from faunadb import query as q
from faunadb.objects import Ref


class FaunaClient(FC):

    def __init__(
            self,
            secret=None,
            domain=env('FAUNA_DOMAIN', 'db.fauna.com'),
            scheme=env('FAUNA_SCHEME', "https"),
            port=None,
            timeout=60,
            observer=None,
            pool_connections=10,
            pool_maxsize=10,
            **kwargs) -> None:
        """
        Args:
          secret (str, required, default=None):
            Auth token for the FaunaDB server.
          domain (str, optional, default="db.fauna.com"):
            Base URL for the FaunaDB server.
          scheme (str, optional, default="https"):
            ``"web"`` or ``"https"``.
          port (int, optional, default=None):
            Port of the FaunaDB server.
          timeout (int, optional, default=60):
            Read timeout in seconds.
          observer (optional, default=None):
            Callback that will be passed a :any:`RequestResult` after every completed request.
          pool_connections (int, optional, default=10):
            The number of connection pools to cache.
          pool_maxsize (int, optional, default=10):
            The maximum number of connections to save in the pool.
            """
        self.secret = secret or env('FAUNA_SECRET')
        env_port = env('FAUNA_PORT')
        if env_port:
            port = int(env_port)
        if not self.secret:
            raise ValueError('When creating a FaunaClient instance you must supply the secret argument or set the '
                             'FAUNA_SECRET environment variable.')  # pragma: no cover

        super(FaunaClient, self).__init__(secret,
                                          domain=domain,
                                          scheme=scheme,
                                          port=port,
                                          timeout=timeout,
                                          observer=observer,
                                          pool_connections=pool_connections,
                                          pool_maxsize=pool_maxsize,
                                          **kwargs)

from faunadb.client import FaunaClient
from faunadb import query as q
from faunadb.objects import Ref
from envs import env


super_client = FaunaClient(secret=env('FAUNA_SUPER_SECRET'))


class Handler(object):

    def __init__(self, config):
        self.config = config
        self.get_connections()

    def get_connections(self):
        try:
            return self._connections
        except AttributeError:
            self._connections = dict()
            for db_label, db_info in self.config.items():
                self._connections[db_label] = FaunaClient(**db_info)
            return self._connections

    def get_client(self, db_label):
        return self._connections[db_label]
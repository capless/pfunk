from faunadb.client import FaunaClient
from faunadb import query as q
from envs import env


super_client = FaunaClient(secret=env('FAUNA_SUPER_SECRET'))

client = FaunaClient(secret=env('FAUNA_SECRET'))

class PFunkHandler(object):
    """
    Example:
    handler = DocbHandler({
        'dynamodb':{
            'connection':{
                'table':'testlocal'
            },
            'documents':['docb.testcase.BaseTestDocumentSlug','docb.testcase.DynamoTestCustomIndex'],
            'config':{
                  'endpoint_url':'http://localhost:8000'
                },
            'table_config':{
                'write_capacity':2,
                'read_capacity':3
            }
        }
    })
    """

    def __init__(self, config):
        self.config = config
        self.get_tables()

    def get_tables(self):
        try:
            return self._tables
        except AttributeError:
            self._tables = dict()
            for db_label, conn in self.get_connections().items():
                self._tables[db_label] = conn.Table(self.config[db_label]['connection']['table'])
            return self._tables

    def get_connections(self):
        try:
            return self._connections
        except AttributeError:
            self._connections = dict()
            for db_label, db_info in self.config.items():
                self._connections[db_label] = boto3.resource(
                    'dynamodb', **db_info.get('config', {}))
            return self._connections

    def get_db(self, db_label):
        return self.get_settings(db_label)

    def get_config(self, db_label):
        return self.get_settings(db_label).get('table_config')

    def get_settings(self, db_label):
        return self.config[db_label]

    def get_connection_info(self, db_label):
        return self.get_settings(db_label).get('connection_info')
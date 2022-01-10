import unittest

import uuid
import os

from valley.utils import import_util
from werkzeug.test import Client
from pfunk import Project
from pfunk.client import FaunaClient, q
from pfunk.template import key_template


class PFunkTestCase(unittest.TestCase):

    def setUp(self) -> None:
        os.environ['PFUNK_TEST_MODE'] = 'True'
        os.environ['TEMPLATE_ROOT_DIR'] = '/tmp'
        self.client = FaunaClient(secret='secret')
        self.db_name = str(uuid.uuid4())
        self.client.query(
            q.create_database({'name': self.db_name})
        )
        self.secret = self.client.query(
            q.create_key({
                "database": q.database(self.db_name),
                "role": "admin"
            })
        ).get('secret')
        os.environ['FAUNA_SECRET'] = self.secret

    def tearDown(self) -> None:
        client = FaunaClient(secret='secret')
        client.query(
            q.delete(q.database(self.db_name))
        )


class CollectionTestCase(PFunkTestCase):
    collections = []

    def setUp(self) -> None:
        super(CollectionTestCase, self).setUp()
        self.project = Project()

        self.project.add_resources(self.collections)
        self.project.publish()


class APITestCase(CollectionTestCase):

    def setUp(self) -> None:
        super(APITestCase, self).setUp()
        self.app = self.project.wsgi_app
        self.c = Client(self.app)
        os.environ.setdefault('KEY_MODULE', 'pfunk.tests.unittest_keys.KEYS')
        Key = import_util('pfunk.contrib.auth.collections.Key')
        keys = Key.create_keys()
        self.keys_path = 'pfunk/tests/unittest_keys.py'
        with open(self.keys_path, 'w+') as f:
            f.write(key_template.render(keys=keys))


    def tearDown(self) -> None:
        super(APITestCase, self).tearDown()
        if os.path.exists(self.keys_path):
            os.remove(self.keys_path)
        else:
            print("The file does not exist")

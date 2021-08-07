import unittest

import uuid
import os
from pfunk import Project
from pfunk.client import FaunaClient, q


class PFunkTestCase(unittest.TestCase):

    def setUp(self) -> None:
        os.environ['PFUNK_TEST_MODE'] = 'True'
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



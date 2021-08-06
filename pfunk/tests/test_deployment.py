from envs import env

from pfunk import FaunaClient
from pfunk.testcase import PFunkTestCase
from pfunk.project import Project
from pfunk.client import q
from pfunk.tests import Sport, Person


class DeploymentTestCase(PFunkTestCase):

    def setUp(self) -> None:
        super(DeploymentTestCase, self).setUp()
        self.project = Project()
        self.project.add_resources([Sport, Person])

    def test_project_publish(self):
        # Make sure collections are created
        collections_before = self.client.query(
            q.paginate(q.collections(q.database(self.db_name)))
        ).get('data')
        self.assertEqual(0, len(collections_before))
        self.project.publish()
        collections_after = self.client.query(
            q.paginate(q.collections(q.database(self.db_name)))
        ).get('data')
        self.assertEqual(2, len(collections_after))
        # Make sure functions are created
        functions = self.client.query(
            q.paginate(q.functions(q.database(self.db_name)))
        ).get('data')

        self.assertEqual(4, len(functions))

        # Make sure indexes are created
        indexes = self.client.query(
            q.paginate(q.indexes(q.database(self.db_name)))
        ).get('data')
        self.assertEqual(3, len(indexes))




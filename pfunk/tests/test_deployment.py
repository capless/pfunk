from pfunk.client import q
from pfunk.contrib.auth.collections.group import Group
from pfunk.contrib.auth.collections.user import User
from pfunk.project import Project
from pfunk.testcase import PFunkTestCase
from pfunk.tests import Sport, Person


class DeploymentTestCase(PFunkTestCase):

    def setUp(self) -> None:
        super(DeploymentTestCase, self).setUp()
        self.project = Project()
        self.project.add_resources([User, Group, Sport, Person])

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

        self.assertEqual(5, len(collections_after))
        # Make sure functions are created
        functions = self.client.query(
            q.paginate(q.functions(q.database(self.db_name)))
        ).get('data')

        self.assertEqual(7, len(functions))

        # Make sure indexes are created
        indexes = self.client.query(
            q.paginate(q.indexes(q.database(self.db_name)))
        ).get('data')
        self.assertEqual(13, len(indexes))
        # Add User and Group to the project
        self.project.add_resources([User, Group])
        # Publish twice more to make sure there are no errors with create_or_update_role or create_or_update_function
        # functions
        self.project.publish()
        self.project.publish()

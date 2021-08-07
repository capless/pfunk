from faunadb.errors import PermissionDenied

from pfunk.tests import User, Group
from pfunk.testcase import CollectionTestCase


class AuthCrudTest(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(AuthCrudTest, self).setUp()
        self.managers = Group.create(name='Managers', slug='managers')
        self.power_users = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                           last_name='Lasso', _credentials='abc123', account_status='ACTIVE', groups=[self.managers])


    def test_create_user(self):
        self.assertEqual(2, len(Group.all()))
        self.assertEqual(1, len(User.all()))
        self.assertIsNotNone(self.user.ref)
        self.assertEqual(self.user.first_name, 'Ted')

    def test_delete(self):
        self.assertEqual(2, len(Group.all()))
        self.assertEqual(1, len(User.all()))
        self.user.delete()
        self.assertEqual(0, len(User.all()))

    def test_update(self):
        self.assertEqual(self.user.username, 'test')
        self.user.username = 'test-c'
        self.user.save()
        u = User.get(self.user.ref.id())
        self.assertEqual(u.username, 'test-c')





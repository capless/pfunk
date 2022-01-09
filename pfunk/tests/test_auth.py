from faunadb.errors import PermissionDenied

from pfunk.contrib.auth.collections import PermissionGroup
from pfunk.tests import User, Group, Sport, Person, House
from pfunk.exceptions import LoginFailed
from pfunk.testcase import CollectionTestCase


class AuthTestCase(CollectionTestCase):
    collections = [User, Group, Sport, Person, House]

    def setUp(self) -> None:
        super(AuthTestCase, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

    def test_login(self):
        token = User.login('test', 'abc123')
        self.assertIsNotNone(token)

        with self.assertRaises(PermissionDenied):
            User.all(_token=token)
        user = User.get_current_user(_token=token)
        self.assertEqual(user.ref, self.user.ref)
        with self.assertRaises(LoginFailed):
            User.login('test', 'wrongpass')

    def test_update_password(self):
        token = User.login('test', 'abc123')
        self.user.update_password('abc123', '123abc', '123abc', _token=token)
        # If the update doesn't work the login call will result in an error
        User.login('test', '123abc')

    def test_create_user_based(self):
        token = User.login('test', 'abc123')
        house = House.create(address='4 Anyview Ln, Hampton, VA 23665', user=self.user, _token=token)
        self.assertEqual(1, len(House.all(_token=token)))

    def test_permissions(self):
        self.assertEqual(self.user.permissions(), [])

        self.user.add_permissions(self.group, [PermissionGroup(House, ['create', 'read', 'write', 'delete'])])
        self.assertEqual(
            self.user.permissions(),
            ['power-users-house-create', 'power-users-house-read', 'power-users-house-write',
             'power-users-house-delete'])

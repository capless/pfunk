from faunadb.errors import PermissionDenied

from pfunk.contrib.auth.collections import PermissionGroup
from pfunk.tests import User, Group, Sport, Person, House
from pfunk.exceptions import LoginFailed
from pfunk.testcase import CollectionTestCase


class AuthTestCase(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(AuthTestCase, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

    def test_login(self):
        # TODO: should test against `pfunk.contrib.auth.views.LoginView`
        pass

    def test_logout(self):
        # TODO: should test againts `pfunk.contrib.auth.views.LogoutView` and invalidate the token
        pass

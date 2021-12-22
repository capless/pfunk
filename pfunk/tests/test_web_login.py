from werkzeug.test import Client
from werkzeug.testapp import test_app
from faunadb.errors import PermissionDenied

from pfunk.contrib.auth.collections import PermissionGroup
from pfunk.tests import User, Group, Sport, Person, House
from pfunk.exceptions import LoginFailed
from pfunk.testcase import CollectionTestCase
from pfunk.contrib.auth.views import LoginView


class TestWebLogin(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(TestWebLogin, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    def test_login(self):
        """ Tests `pfunk.contrib.auth.views.LoginView` to return a JWT """
        res = self.c.post('/user/login/',
                          json={"username": "test", "password": "abc123"})

        # check if response has cookies
        self.assertIsNotNone(res.headers['Set-Cookie'])
        self.assertTrue(res.json['success'])

    def test_wrong_login(self):
        """ Tests `pfunk.contrib.auth.views.LoginView` to return an exception when credentials are wrong """
        res = self.c.post('/user/login/',
                          json={"username": "test", "password": "abc123"})

        self.assertRaises(LoginFailed)

    def test_logout(self):
        """ Tests `pfunk.contrib.auth.views.LogoutView` invalidate token login and remove cookie """
        token, exp = User.api_login("test", "abc123")
        res = self.c.post('/user/logout/', headers={
            "Authorization": token,
            "Content-Type": "application/json"
        })

        self.assertTrue(res.json['success'])

    def test_wrong_logout(self):
        """ Tests `pfunk.contrib.auth.views.LogoutView` to return an exception trying to logout a nonexistent token """
        token = ''
        res = self.c.post('/user/logout/', headers={
            "Authorization": token,
            "Content-Type": "application/json"
        })
        expected = {'success': False, 'data': 'Unauthorized'}
        self.assertDictEqual(expected, res.json)

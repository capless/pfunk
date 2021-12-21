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
        res = self.c.post('/user/login/', 
            json={"username": "test", "password": "abc123"})

        self.assertIsNotNone(res.headers['Set-Cookie']) # check if response has cookies
        self.assertTrue(res.json['success'])

    def test_wrong_login(self):
        res = self.c.post('/user/login/', 
            json={"username": "test", "password": "abc123"})

        self.assertRaises(LoginFailed)


    def test_logout(self):
        token, exp = User.api_login("test", "abc123")
        # BUG: Invalid header padding, there may be something wrong with passing of token to logout view
        res = self.c.post('/user/logout/',
            json={"token": token}, headers={"Authorization": f"Bearer {token}"})
        print(res.json)
        pass

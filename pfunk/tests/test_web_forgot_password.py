from re import S
from werkzeug.test import Client

from pfunk.tests import User, Group
from pfunk.testcase import CollectionTestCase


class TestWebForgotPassword(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(TestWebForgotPassword, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.app = self.project.wsgi_app
        self.c = Client(self.app)
        self.token, self.exp = User.api_login("test", "abc123")

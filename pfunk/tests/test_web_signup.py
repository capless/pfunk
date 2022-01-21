from werkzeug.test import Client

from pfunk.tests import User, Group 
from pfunk.testcase import APITestCase


class TestWebSignup(APITestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(TestWebSignup, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    def test_signup(self):
        """ Tests `pfunk.contrib.auth.views.SignUpView` to successfully sign up a new user 
        
            Will not login the user, `INACTIVE` users cannot log in by default using
            `login_user` Fauna function
        """
        res = self.c.post('/user/sign-up/', json={
            "username": "new_user",
            "email": "testemail@email.com",
            "first_name": "Forest",
            "last_name": "Gump",
            "_credential_field": "password" 
        })

        # token = User.login(username="new_user", password="password")
        self.assertTrue(res.json['success'])
        self.assertIn("new_user", [user.username for user in User.all()])

    def test_signup_not_unique(self):
        """ Tests `pfunk.contrib.auth.views.SignUpView` to return a not unique json error """
        res = self.c.post('/user/sign-up/', json={
            "username": "test",
            "email": "testemail@email.com",
            "first_name": "Forest",
            "last_name": "Gump",
            "_credential_field": "password" 
        })

        self.assertFalse(res.json['success'])
        self.assertEqual('document is not unique.', res.json['data'])

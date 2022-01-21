from werkzeug.test import Client

from pfunk.tests import User, Group
from pfunk.testcase import APITestCase


class TestWebForgotPassword(APITestCase):
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
        self.user.attach_forgot_verification_key()
        self.key = self.user.forgot_password_key

    def test_send_forgot_req(self):
        res = self.c.post(f'/user/forgot-password/',
                          json={"email": "tlasso@example.org"},
                          headers={
                              "Content-Type": "application/json"})

        self.assertTrue(res.json['success'])
    
    def test_submit_key_for_forgot_pass(self):
        """ Submits the key from the forgot password email to initiate password reset """
        
        res = self.c.put(f'/user/forgot-password/',
                          json={
                              "verification_key": self.key,
                              "password": "new_updated_pass"},
                          headers={
                              "Content-Type": "application/json"})

        new_login = User.api_login("test", "new_updated_pass")
        self.assertTrue(res.json['success'])
        self.assertIsNotNone(new_login)

    def test_submit_wrong_key_for_forgot_pass(self):
        """ Submit a wrong key for verification of reset password. Should return `Not Found` """
        key = 'wrong-key'
        res = self.c.put(f'/user/forgot-password/',
                          json={
                              "verification_key": key,
                              "password": "forgotten_password"},
                          headers={
                              "Content-Type": "application/json"})
        expected = {'data': 'Not Found', 'success': False}

        self.assertFalse(res.json['success'])
        self.assertDictEqual(res.json, expected)

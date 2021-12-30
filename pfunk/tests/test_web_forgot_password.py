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

    def test_send_forgot_req(self):
        res = self.c.post(f'/user/forgot-password/',
                          json={"email": "tlasso@example.org"},
                          headers={
                              "Content-Type": "application/json"})

        self.assertTrue(res.json['success'])
    
    def test_submit_key_for_forgot_pass(self):
        """ Submits the key from the forgot password email to initiate password reset """
        # TODO: create endpoint for accepting the verification key and initiating password reset
        key = ''
        res = self.c.get(f'/user/forgot-password/?key={key}',
                          json={"email": "tlasso@example.org"},
                          headers={
                              "Content-Type": "application/json"})

        self.assertTrue(res.json['success'])

    def test_submit_wrong_key_for_forgot_pass(self):
        # TODO: create endpoint for accepting the verification key and initiating password reset
        key = ''
        res = self.c.get(f'/user/forgot-password/?key={key}',
                          json={"email": "tlasso@example.org"},
                          headers={
                              "Content-Type": "application/json"})
        expected = {
            'success': False,
            'data': 'wrong verification key'
        }

        self.assertFalse(res.json['success'])
        self.assertDictEqual(res.json, expected)

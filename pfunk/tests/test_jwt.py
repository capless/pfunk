from faunadb.errors import PermissionDenied

from pfunk.contrib.auth.collections import Key
from pfunk.tests import User, Group
from pfunk.exceptions import LoginFailed
from pfunk.testcase import APITestCase
from pfunk.contrib.auth.collections import Key


class AuthToken(APITestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(AuthToken, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Mr. Auth',
                                last_name='Broski', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

    def test_generate_token(self):
        token = Key.create_jwt('secret')
        api_login_token = User.api_login('test', 'abc123')

        self.assertIsNotNone(token)
        self.assertIsNotNone(api_login_token)

    def test_decrypt_token(self):
        claims = {
            'token': 'token',
            'permissions': ['read'],
            'user': {'username': 'test'}
        }
        # `create_jwt` returns both jwt and exp, only get the jwt
        token = Key.create_jwt(claims)[0]
        decrypted_token = Key.decrypt_jwt(encoded=token)

        # the value should be the same
        self.assertEqual(claims, decrypted_token)

    def test_api_login(self):
        token = User.api_login('test', 'abc123')
        self.assertIsNotNone(token)

        with self.assertRaises(LoginFailed):
            User.login('test', 'wrongpass')

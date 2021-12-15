from pfunk.contrib.auth.collections import Key
from pfunk.contrib.auth.collections import PermissionGroup
from pfunk.tests import User, Group, Sport, Person, House
from pfunk.exceptions import LoginFailed
from pfunk.testcase import CollectionTestCase
from pfunk.contrib.auth.collections import Key


class AuthToken(CollectionTestCase):
    collections = [User, Group]
    def setUp(self) -> None:
        super(AuthToken, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

    def test_generate_token(self):
        # generation of token should work
        token = Key.create_jwt('secret')
        api_login_token = User.api_login('test', 'abc123')

        self.assertIsNotNone(token) 
        self.assertIsNotNone(api_login_token) 

    def test_decrypt_token(self):
        secret = {
            'token': 'token',
            'permissions': ['read'],
            'user': { 'username': 'test' }
        }
        token = Key.create_jwt(secret)
        decrypted_token = Key.decrypt_jwt(token)
        # the value should be the same
        self.assertEqual(secret, decrypted_token)

    def test_import_keys(self):
        # TODO: There should be no errors in importing the keys needed
        assert(True)

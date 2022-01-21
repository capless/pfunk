from pfunk.tests import User, Group
from pfunk.testcase import APITestCase


class TestWebChangePassword(APITestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(TestWebChangePassword, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

        self.token, self.exp = User.api_login("test", "abc123")

    def test_update_password(self):
        """ Tests `pfunk.contrib.auth.views.UpdatePasswordView` to change a user's current password """
        res = self.c.post('/user/update-password/',
                          json={
                              "current_password": "abc123",
                              "new_password": "updated_password",
                              "new_password_confirm": "updated_password"
                          },
                          headers={
                              "Authorization": self.token
                          })
        
        new_token, new_exp = User.api_login("test", "updated_password")

        self.assertIsNotNone(new_token)
        self.assertTrue(res.json['success'])
    
    def test_update_pass_wrong_current(self):
        """ Tests `pfunk.contrib.auth.views.UpdatePasswordView` throw an error if the current password given was wrong """
        res = self.c.post('/user/update-password/',
                          json={
                              "current_password": "wrong_current_password",
                              "new_password": "updated_password",
                              "new_password_confirm": "updated_password"
                          },
                          headers={
                              "Authorization": self.token
                          })
        expected = {'success': False, 'data': {'validation_errors': {'current_password': ' Password update failed.'}}}
        
        self.assertDictEqual(res.json, expected)
        self.assertFalse(res.json['success'])

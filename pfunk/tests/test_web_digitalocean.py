from pfunk.tests import User, Group
from pfunk.testcase import APITestCase


class TestWebDigitalOcean(APITestCase):
    collections = [User, Group]

    
    def setUp(self) -> None:
        super().setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])

        self.token, self.exp = User.api_login("test", "abc123")
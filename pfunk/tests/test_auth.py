from pfunk.contrib.auth.collections import User, Group
from pfunk.testcase import CollectionTestCase


class AuthTestCase(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(AuthTestCase, self).setUp()
        self.user = User.create
    def test_login(self):
        pass

    def test_get_from_id(self):
        pass

    def test_update_password(self):
        pass


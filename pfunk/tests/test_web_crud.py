from werkzeug.test import Client

from pfunk.tests import User, Group
from pfunk.exceptions import LoginFailed
from pfunk.testcase import APITestCase
from pfunk.tests import House


class TestWebCrud(APITestCase):
    collections = [User, Group, House]

    def setUp(self) -> None:
        super(TestWebCrud, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.token, self.exp = User.api_login("test", "abc123")
        self.house = House.create(address="test address", user=self.user)
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    def test_read(self):
        res = self.c.get(f'/house/detail/{self.house.ref.id()}/',
                         headers={
                             "Authorization": self.token})
        self.assertTrue(res.json['success'])
        self.assertEqual("test address", res.json['data']['data']['address'])

    def test_read_all(self):
        res = self.c.get(f'/house/list/',
                         headers={
                             "Authorization": self.token})
        self.assertTrue(res.json['success'])

    def test_create(self):
        self.assertNotIn("the street somewhere", [
            house.address for house in House.all()])
        res = self.c.post('/house/create/',
                          json={
                              "address": "the street somewhere",
                              "user": self.user.ref.id()},
                          headers={
                              "Authorization": self.token})

        self.assertTrue(res.json['success'])
        self.assertIn("the street somewhere", [
                      house.address for house in House.all()])

    def test_update(self):
        self.assertNotIn("the updated street somewhere", [
            house.address for house in House.all()])
        res = self.c.put(f'/house/update/{self.house.ref.id()}/',
                         json={
                             "address": "the updated street somewhere",
                             "user": self.user.ref.id()},
                         headers={
                             "Authorization": self.token})

        self.assertTrue(res.json['success'])
        self.assertIn("the updated street somewhere", [
                      house.address for house in House.all()])

    def test_delete(self):
        res = self.c.delete(f'/house/delete/{self.house.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })

        self.assertTrue(res.json['success'])

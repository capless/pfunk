from werkzeug.test import Client

from pfunk.contrib.auth.collections import Group
from pfunk.contrib.auth.collections import User
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
        self.house_b = House.create(address="test another address", user=self.user)
        self.house_b = House.create(address="test even another address", user=self.user)
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    def test_read(self):
        res = self.c.get(f'/house/detail/{self.house.ref.id()}/',
                         headers={
                             "Authorization": self.token})

        self.assertIn("test address", res.text)

    def test_read_all(self):
        res = self.c.get(f'/house/list/',
                         headers={
                             "Authorization": self.token})
        self.assertTrue(res.status_code, 200)
        self.assertIn("test address", str(res.text))
        self.assertIn("test another address", str(res.text))
        self.assertIn("test even another address", str(res.text))

    def test_create(self):
        self.assertNotIn("the street somewhere", [
            house.address for house in House.all()])
        res = self.c.post('/house/create/',
                          data={
                              "address": "the street somewhere",
                              "user": self.user.ref.id()},
                          headers={
                              "Authorization": self.token})

        self.assertIn("the street somewhere", [
            house.address for house in House.all()])
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.location, "/house/list/")

    def test_update(self):
        self.assertNotIn("the updated street somewhere", [
            house.address for house in House.all()])
        res = self.c.post(f'/house/update/{self.house.ref.id()}/',
                          data={
                              "address": "the updated street somewhere",
                              "user": self.user.ref.id()},
                          headers={
                              "Authorization": self.token})
        self.assertIn("the updated street somewhere", [
            house.address for house in House.all()])

    def test_delete(self):
        self.assertIn("test address", [
            house.address for house in House.all()])
        res = self.c.get(f'/house/delete/{self.house.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })
        self.assertEqual(res.status_code, 200)
        self.assertIn("Delete test address", str(res.text))
        res = self.c.post(f'/house/delete/{self.house.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.location, "/house/list/")
        self.assertNotIn("the address", [
            house.address for house in House.all()])




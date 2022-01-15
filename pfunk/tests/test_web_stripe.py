from werkzeug.test import Client

from pfunk.tests import User, Group
from pfunk.contrib.auth.collections import PermissionGroup
from pfunk.contrib.ecommerce.collections import StripePackage, StripeCustomer
from pfunk.testcase import APITestCase


class TestWebStripe(APITestCase):
    # TODO: Add `StripeCustomer`
    collections = [User, Group, StripePackage]

    def setUp(self) -> None:
        super(TestWebStripe, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.stripe_pkg = StripePackage.create(
            stripe_id='100', price='10', description='unit testing...', name='unit test package')
        # self.stripe_customer = StripeCustomer.create(user=self.user, customer_id='100', package=self.stripe_pkg)

        self.token, self.exp = User.api_login("test", "abc123")
        self.app = self.project.wsgi_app
        self.c = Client(self.app)
        # self.user.add_permissions(self.group, [PermissionGroup(StripePackage, ['create', 'read', 'write', 'delete'])])

    def test_list_package(self):
        res = self.c.get('/stripepackage/list/', headers={
            "Content-Type": "application/json"
        })
        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data'][0]['data']['name'],
            self.stripe_pkg.name)

    def test_get_package(self):
        res = self.c.get(f'/stripepackage/detail/{self.stripe_pkg.ref.id()}/', headers={
            "Content-Type": "application/json"
        })
        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data']['name'],
            self.stripe_pkg.name)

    # TODO: Fix `forbidden` error in stripe views
    def test_create_package(self):
        res = self.c.post('/stripepackage/create/',
                          json={
                              'stripe_id': '123',
                              'name': 'stripe_pkg',
                              'price': 10.10,
                              'description': 'a test package'
                          },
                          headers={
                              "Authorization": self.token,
                              "Content-Type": "application/json"
                          })



    # TODO: Fix `forbidden` error in stripe views
    def test_update_package(self):
        res = self.c.put(f'/stripepackage/update/{self.stripe_pkg.ref.id()}/',
                          json={
                              'stripe_id': '123',
                              'name': 'stripe_pkg',
                              'price': 10.10,
                              'description': 'a test package'
                          },
                          headers={
                              "Authorization": self.token,
                              "Content-Type": "application/json"
                          })



    # TODO: Fix `forbidden` error in stripe views
    def test_delete_package(self):
        res = self.c.delete(f'/stripepackage/delete/{self.stripe_pkg.ref.id()}/',
                          headers={
                              "Authorization": self.token,
                              "Content-Type": "application/json"
                          })

        
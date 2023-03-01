from types import SimpleNamespace
from unittest import mock

from werkzeug.test import Client

from pfunk.contrib.auth.collections import Group, User, UserGroups
from pfunk.contrib.auth.key import PermissionGroup
from pfunk.contrib.ecommerce.collections import StripePackage, StripeCustomer
from pfunk.contrib.ecommerce.views import BaseWebhookView
from pfunk.testcase import APITestCase
from pfunk.web.request import HTTPRequest


class TestWebStripeCrud(APITestCase):
    collections = [User, Group, UserGroups, StripePackage, StripeCustomer]

    def setUp(self) -> None:
        super(TestWebStripeCrud, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.stripe_pkg = StripePackage.create(group=self.group,
                                               stripe_id='100', price='10', description='unit testing...',
                                               name='unit test package')
        self.stripe_cus = StripeCustomer.create(
            user=self.user, stripe_id='100')

        self.token, self.exp = User.api_login("test", "abc123")
        self.app = self.project.wsgi_app
        self.c = Client(self.app)
        self.user.add_permissions(self.group, [PermissionGroup(
            StripePackage, ['create', 'read', 'write', 'delete'])])

    def test_list_package(self):
        res = self.c.get('/json/stripepackage/list/', headers={
            "Content-Type": "application/json"
        })
        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data'][0]['data']['name'],
            self.stripe_pkg.name)

    def test_get_package(self):
        res = self.c.get(f'/json/stripepackage/detail/{self.stripe_pkg.ref.id()}/', headers={
            "Content-Type": "application/json"
        })
        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data']['name'],
            self.stripe_pkg.name)

    def test_create_package(self):
        self.assertNotIn("new stripe pkg", [
            pkg.name for pkg in StripePackage.all()])
        res = self.c.post('/json/stripepackage/create/',
                          json={
                              'stripe_id': '123',
                              'name': 'new stripe pkg',
                              'price': 10.10,
                              'description': 'a test package',
                              'group': self.group.ref.id()
                          },
                          headers={
                              "Authorization": self.token
                          })

        self.assertTrue(res.json['success'])
        self.assertIn("new stripe pkg", [
            pkg.name for pkg in StripePackage.all()])

    def test_update_package(self):
        self.assertNotIn("updated pkg", [
            pkg.name for pkg in StripePackage.all()])
        updated_name = 'updated pkg'
        res = self.c.put(f'/json/stripepackage/update/{self.stripe_pkg.ref.id()}/',
                         json={
                             'stripe_id': '123',
                             'name': updated_name,
                             'price': 10.10,
                             'description': 'a test package'
                         },
                         headers={
                             "Authorization": self.token,
                             "Content-Type": "application/json"
                         })

        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data']['name'],
            updated_name)

    def test_delete_package(self):
        res = self.c.delete(f'/json/stripepackage/delete/{self.stripe_pkg.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })

        self.assertTrue(res.json['success'])
        self.assertNotIn(
            self.stripe_pkg.ref.id(),
            [pkg.ref.id() for pkg in StripePackage.all()]
        )

    def test_create_customer(self):
        stripe_id = '201'
        self.assertNotIn(stripe_id, [
            cus.stripe_id for cus in StripeCustomer.all()])
        res = self.c.post(f'/json/stripecustomer/create/',
                          json={
                              "user": self.user.ref.id(),
                              "stripe_id": stripe_id
                          },
                          headers={
                              "Authorization": self.token,
                              "Content-Type": "application/json"
                          })

        self.assertTrue(res.json['success'])
        self.assertIn(stripe_id, [
            cus.stripe_id for cus in StripeCustomer.all()])

    def test_list_customers(self):
        res = self.c.get('/json/stripecustomer/list/', headers={
            "Authorization": self.token,
            "Content-Type": "application/json"
        })

        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data'][0]['data']['stripe_id'],
            '100')

    def test_get_customer(self):
        res = self.c.get(f'/json/stripecustomer/detail/{self.stripe_cus.ref.id()}/', headers={
            "Authorization": self.token,
            "Content-Type": "application/json"
        })

        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data']['stripe_id'],
            '100')

    def test_update_customer(self):
        updated_stripe_id = '101'
        self.assertNotIn(updated_stripe_id, [
            cus.stripe_id for cus in StripeCustomer.all()])
        res = self.c.put(f'/json/stripecustomer/update/{self.stripe_cus.ref.id()}/',
                         json={
                             "stripe_id": updated_stripe_id
                         },
                         headers={
                             "Authorization": self.token,
                             "Content-Type": "application/json"
                         })

        self.assertTrue(res.json['success'])
        self.assertEqual(
            res.json['data']['data']['stripe_id'],
            updated_stripe_id)

    def test_delete_customer(self):
        res = self.c.delete(f'/json/stripecustomer/delete/{self.stripe_cus.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })

        self.assertTrue(res.json['success'])
        self.assertNotIn(
            self.stripe_cus.ref.id(),
            [cus.ref.id() for cus in StripeCustomer.all()]
        )


class TestStripeWebhook(APITestCase):
    collections = [User, Group, UserGroups, StripeCustomer]

    def setUp(self) -> None:
        super(TestStripeWebhook, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.token, self.exp = User.api_login("test", "abc123")
        self.app = self.project.wsgi_app
        self.view = BaseWebhookView()
        self.stripe_req_body = {
            "id": "evt_1CiPtv2eZvKYlo2CcUZsDcO6",
            "object": "event",
            "api_version": "2018-05-21",
            "created": 1530291411,
            "data": {
                "object": {}
            },
            "livemode": False,
            "pending_webhooks": 0,
            "request": {
                "id": None,
                "idempotency_key": None
            },
            "type": "source.chargeable"
        }
        headers = {'HTTP_STRIPE_SIGNATURE': 'sig_112233'}
        event = {
            'body': self.stripe_req_body,
            'requestContext': {
                'web': {
                    'method': 'post',
                    'path': '/webhook',
                    'source_ip': '192.168.1.30'
                }
            },
            'headers': headers
        }
        self.view.request = HTTPRequest(event=event)
        self.c = Client(self.app)

    def test_event_action(self):
        # event_dict = {'type': 'checkout.session.completed'}
        with self.assertRaises(NotImplementedError):
            self.view.event = SimpleNamespace(**self.view.request.body)
            res = self.view.event_action()

    def test_check_ip(self):
        res = self.view.check_ip()
        self.assertFalse(res)

    @mock.patch('boto3.client')
    def test_send_html_email(self, mocked):
        # Requires to have `TEMPLATE_ROOT_DIR=/tmp` in your .env file
        res = self.view.send_html_email(
            subject='Test Subject',
            from_email='unittesting@email.com',
            to_email_list=['recipient@email.com'],
            template_name=('email/email_template.html')
        )
        self.assertTrue(True)  # if there are no exceptions, then it passed

    @mock.patch('stripe.Webhook')
    def test_check_signing_secret(self, mocked):
        res = self.view.check_signing_secret()
        self.assertTrue(True)  # if there are no exceptions, then it passed

    def test_get_transfer_data(self):
        self.view.event_json = self.view.request.body
        res = self.view.get_transfer_data()
        self.assertTrue(True)

    @mock.patch('stripe.Webhook')
    def test_receive_post_req(self, mocked):
        with self.assertRaises(NotImplementedError):
            self.view.event = SimpleNamespace(**self.view.request.body)
            res = self.c.post('/json/stripecustomer/webhook/',
                              json=self.stripe_req_body,
                              headers={
                                  'HTTP_STRIPE_SIGNATURE': 'sig_1113'
                              })


class TestStripeCheckoutView(APITestCase):
    collections = [User, Group, UserGroups, StripePackage]

    def setUp(self) -> None:
        super(TestStripeCheckoutView, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.token, self.exp = User.api_login("test", "abc123")
        self.stripe_pkg = StripePackage.create(group=self.group,
                                               stripe_id='100', price='10', description='unit testing...',
                                               name='unit test package')
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    @mock.patch('stripe.checkout', spec=True)
    def test_checkout_success_view(self, mocked):
        session_id = 'session_123'
        res = self.c.get(f'/json/stripepackage/checkout-success/{session_id}/', headers={
            'Authorization': self.token,
            'Content-Type': 'application/json'
        })

        self.assertTrue(True)
        self.assertDictEqual({'success': False, 'data': 'Not Found'}, res.json)
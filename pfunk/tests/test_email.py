import tempfile
from werkzeug.test import Client
from unittest import mock
import os
from jinja2.exceptions import TemplateNotFound

from pfunk.tests import User, Group
from pfunk.testcase import CollectionTestCase
from pfunk.contrib.email.ses import SESBackend 
from pfunk.contrib.email.base import EmailBackend


class TestEmailBackend(CollectionTestCase):
    collections = [User, Group]

    def setUp(self) -> None:
        super(TestEmailBackend, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.backend = EmailBackend()
        self.app = self.project.wsgi_app
        os.environ['TEMPLATE_ROOT_DIR'] = '/tmp'
        self.c = Client(self.app)

    def test_get_template(self):
        # TODO: Create a tempfile to be able to use with JInja2 template loader
        with tempfile.NamedTemporaryFile(suffix='.html') as tmp:\
            self.backend.get_template(tmp.name)
        self.assertTrue()

    def test_get_wrong_template(self):
        with self.assertRaises(TemplateNotFound):
            self.backend.get_template('youWillNotFindMe.html')

    def test_send_email(self):
        with self.assertRaises(NotImplementedError):
            self.backend.send_email()

    def test_get_body(self):
        # TODO: Create a tempfile to be able to use with JInja2 template loader
        with tempfile.NamedTemporaryFile(suffix='.html') as tmp:
            rendered = self.backend.get_body_kwargs()
        
        self.assertIsNotNone(rendered)


# TODO: Mock SES Methods for unit testing

# class TestEmailSES(CollectionTestCase):
#     collections = [User, Group]

#     def setUp(self) -> None:
#         super(TestEmailSES, self).setUp()
#         self.group = Group.create(name='Power Users', slug='power-users')
#         self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
#                                 last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
#                                 groups=[self.group])
#         self.SES = SESBackend()
#         self.c = Client(self.app)

#     @mock.patch('boto3.client')
#     def test_send_email(self):
#         res = self.SES.send_email(
#             subject="test", 
#             to_emails=["testemail@email.com"], 
#             html_template="testhtmlhtml", 
#             txt_template="test.txt",
#             from_email="testFromEmail@email.com", 
#             cc_emails=["testCCemail@email.com"], 
#             bcc_emails=["testBCCemail@email.com"], 
#         )
#         print(res)
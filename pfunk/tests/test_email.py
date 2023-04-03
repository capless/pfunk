import os
import tempfile
from unittest import mock

from jinja2.exceptions import TemplateNotFound
from werkzeug.test import Client

from pfunk.contrib.auth.collections import Group, User, UserGroups
from pfunk.contrib.email.base import EmailBackend
from pfunk.contrib.email.ses import SESBackend
from pfunk.testcase import APITestCase


class TestEmailBackend(APITestCase):
    collections = [User, Group, UserGroups]

    def setUp(self) -> None:
        # NOTE: env var TEMPLATE_ROOT_DIR should be set to "/"
        super(TestEmailBackend, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.backend = EmailBackend()

    def test_get_template(self):
        template = self.backend.get_template(
            '/code/pfunk/tests/templates/email/email_template.html')
        # test jinja render if no exceptions
        template.render(unittest_value="random value")
        self.assertTrue(True)  # if there are no exceptions, then it is a pass

    def test_get_wrong_template(self):
        with self.assertRaises(TemplateNotFound):
            self.backend.get_template('youWillNotFindMe.html')

    def test_send_email(self):
        with self.assertRaises(NotImplementedError):
            self.backend.send_email()

    def test_get_body(self):
        with tempfile.NamedTemporaryFile(suffix='.html') as tmp:
            rendered = self.backend.get_body_kwargs()

        self.assertIsNotNone(rendered)


class TestEmailSES(APITestCase):
    collections = [User, Group, UserGroups]

    def setUp(self) -> None:
        super(TestEmailSES, self).setUp()
        self.group = Group.create(name='Power Users', slug='power-users')
        self.user = User.create(username='test', email='tlasso@example.org', first_name='Ted',
                                last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                groups=[self.group])
        self.SES = SESBackend()
        self.app = self.project.wsgi_app
        self.c = Client(self.app)

    @mock.patch('boto3.client')
    def test_send_email(self, mocked):
        res = self.SES.send_email(
            subject="test",
            to_emails=["testemail@email.com"],
            html_template='code/pfunk/tests/templates/email/email_template.html',
            from_email="testFromEmail@email.com",
            cc_emails=["testCCemail@email.com"],
            bcc_emails=["testBCCemail@email.com"],
        )

        # if there are no exceptions, then it's a passing test
        self.assertTrue(True)

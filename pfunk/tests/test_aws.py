import unittest
from unittest import mock

from pfunk.utils.aws import ApiGateway
from pfunk.tests import User, Group, Person, Sport
from pfunk.project import Project


class ApiGatewayTests(unittest.TestCase):

    @classmethod
    def setUpCls(cls) -> None:
        cls.project = Project()
        cls.aws_client = ApiGateway()
        cls.project.add_resources([Person, Sport, Group, User])
        cls.api_yaml = cls.project.generate_swagger()

    def test_validate_yaml(self):
        result = self.aws_client.validate_yaml(self.api_yaml)
        self.assertIsNone(result)  # if there are no errors, then spec is valid

    def test_validate_wrong_yaml(self):
        result = self.aws_client.validate_yaml('wrong yaml...33::39')
        self.assertIsNotNone(result)  # if there are returned objs, there is an error

    @mock.patch('boto3.client')
    def test_create_api_from_yaml(self):
        result = self.aws_client.create_api_from_yaml()
        self.assertTrue(result['success'])

    @mock.patch('boto3.client')
    def test_update_api_from_yaml(self):
        result = self.aws_client.create_api_from_yaml()
        self.assertTrue(result['success'])

    def test_create_api_from_wrong_yaml(self):
        result = self.aws_client.create_api_from_yaml('wrong yaml...21320:: asdkas')
        self.assertEqual(result, 'Bad Request. YAML is not valid.')

    def test_update_api_from_wrong_yaml(self):
        result = self.aws_client.update_api_from_yaml('wrong yaml...21320:: asdkas')
        self.assertEqual(result, 'Bad Request. YAML is not valid.')
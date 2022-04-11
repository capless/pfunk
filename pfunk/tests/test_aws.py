import os
import unittest
import tempfile
from unittest import mock

from pfunk.utils.aws import ApiGateway
from pfunk.tests import User, Group, Person, Sport
from pfunk.project import Project


class ApiGatewayTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.project = Project()
        cls.aws_client = ApiGateway()
        cls.project.add_resources([Person, Sport, Group, User])

        swagger = cls.project.generate_swagger()
        cls.swagger_dir = swagger['dir']
        cls.swagger_file = swagger['swagger_file']

    def test_validate_yaml(self):
        result = self.aws_client.validate_yaml(self.swagger_dir)
        self.assertIsNone(result)  # if there are no errors, then spec is valid

    def test_validate_wrong_yaml(self):
        result = self.aws_client.validate_yaml('wrong yaml...33::39')
        # if there are returned objs, there is an error
        self.assertIsNotNone(result)

    @mock.patch('boto3.client')
    def test_create_api_from_yaml(self, mocked):
        result = self.aws_client.create_api_from_yaml(
            yaml_file=self.swagger_dir)
        self.assertTrue(result['success'])

    @mock.patch('boto3.client')
    def test_create_api_from_wrong_yaml(self, mocked):
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w') as tmp:
            tmp.seek(0)
            tmp.write('test wrong yaml')
            result = self.aws_client.create_api_from_yaml(tmp.name)
        self.assertEqual(result['error'], 'Bad Request. YAML is not valid.')

    # @mock.patch('boto3.client')
    # def test_update_api_from_yaml(self):
    #     result = self.aws_client.update_api_from_yaml(yaml_file=self.api_yaml)
    #     self.assertTrue(result['success'])

    # def test_update_api_from_wrong_yaml(self):
    #     result = self.aws_client.update_api_from_yaml('wrong yaml...21320:: asdkas')
    #     self.assertEqual(result, 'Bad Request. YAML is not valid.')

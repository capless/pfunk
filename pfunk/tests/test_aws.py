import os
import unittest
import tempfile
from unittest import mock

from pfunk.utils.aws import ApiGateway
from pfunk.tests import User, Group, Person, Sport
from pfunk.project import Project


class ApiGatewayTests(unittest.TestCase):
    """ Unit tests for creation of API from Swagger file 
    
        Note that the unittests uses mocked boto3 normally. If
        you want to test against a real endpoint, remove the 
        patch decorator at `setUpClass` and the `mocked` 
        param. Also make sure you have the required
        env vars for AWS credentials and you have
        the json config in the current env.
    """

    @classmethod
    @mock.patch('boto3.client')
    def setUpClass(cls, mocked) -> None:
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

    @mock.patch('boto3.client')
    def test_update_api_from_yaml(self, mocked):
        result = self.aws_client.update_api_from_yaml(
            yaml_file=self.swagger_dir, mode='merge')
        self.assertTrue(result['success'])

    @mock.patch('boto3.client')
    def test_update_api_from_wrong_yaml(self, mocked):
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w') as tmp:
            tmp.seek(0)
            tmp.write('test wrong yaml')
            result = self.aws_client.update_api_from_yaml(tmp.name, mode='merge')
        self.assertEqual(result['error'], 'Bad Request. YAML is not valid.')

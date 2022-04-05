import unittest

from pfunk.utils.aws import ApiGateway
from pfunk.tests import User, Group
from pfunk.project import Project


class ApiGatewayTests(unittest.TestCase):

    def setUp(self) -> None:
        self.project = Project()

    def test_validate_yaml(self):
        pass

    def test_create_api_from_yaml(self):
        pass

    def test_update_api_from_yaml(self):
        pass

import json
import os
import unittest

from pfunk.cli import init
from pfunk.project import Project
from pfunk.tests import Person, Sport, GENDER_PRONOUN
from pfunk.contrib.auth.collections import User
from pfunk.contrib.auth.collections import Group


class ProjectTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.project = Project()
        with open(f'pfunk.json', 'x') as f:
            json.dump({
                'name': 'test',
                'api_type': 'rest',
                'description': 'test project',
                'host': 'localhost',
                'stages': {'dev': {
                    'key_module': f'test.dev_keys.KEYS',
                    'fauna_secret': 'test-key',
                    'bucket': 'test-bucket',
                    'default_from_email': 'test@example.org'
                }}
            }, f, indent=4, sort_keys=True)

    def tearDown(self) -> None:
        os.remove("pfunk.json")
        # try:
        #     os.remove('swagger.yaml')
        # except FileNotFoundError:
        #     pass

    def test_add_resource(self):
        self.project.add_resource(Person)
        self.project.add_resource(Person)
        # Test that no duplicates are there
        self.assertEqual(self.project.collections, set([Person]))

    def test_add_resources(self):
        self.project.add_resources([Person, Sport])
        self.assertEqual(self.project.collections, set([Person, Sport]))

    def test_render(self):
        self.project.add_resources([Person, Sport])
        gql = self.project.render()
        self.assertEqual(self.project.enums, set([GENDER_PRONOUN]))
        self.assertTrue('enum gender_pronouns' in gql)
        self.assertTrue('type Person' in gql)
        self.assertTrue('type Sport' in gql)
        self.assertTrue('allPeople: [Person] @index(name: "all_people")' in gql)

    def test_swagger(self):
        self.project.add_resources([Person, Sport, Group, User])
        self.project.generate_swagger()
        self.assertTrue(True) # if there are no exceptions, then it passed
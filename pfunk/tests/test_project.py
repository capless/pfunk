import unittest
from pfunk.project import Project
from pfunk.tests import Person, Sport, GENDER_PRONOUN


class ProjectTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.project = Project()

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



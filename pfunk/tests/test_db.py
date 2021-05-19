import unittest
from pfunk.db import Database
from pfunk.tests import Person, Sport, GENDER_PRONOUN


class DBTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.db = Database(name='test')

    def test_add_resource(self):
        self.db.add_resource(Person)
        self.assertEqual(self.db._collection_list, [Person])

    def test_add_resources(self):
        self.db.add_resources([Person, Sport])
        self.assertEqual(self.db._collection_list, [Person, Sport])

    def test_render(self):
        self.db.add_resources([Person, Sport])
        gql = self.db.render()
        self.assertEqual(self.db._enum_list, [GENDER_PRONOUN])
        self.assertTrue('enum gender_pronouns' in gql)
        self.assertTrue('type Person' in gql)
        self.assertTrue('type Sport' in gql)
        self.assertTrue('allPeople: [Person] @index(name: "all_people")' in gql)



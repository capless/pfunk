import unittest
from envs import env

from pfunk import Collection, StringField, IntegerField, DateField, DateTimeField, BooleanField, FloatField
from pfunk.indexes import Index
from pfunk.db import Database

from pfunk.loading import PFunkHandler


class TestPfunk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Database(name='capless-dev')

    @classmethod
    def tearDownClass(cls):
        cls.d = None
        
    def test_index(self):
        # Assemble
        NAME = "age-index"
        SOURCE = 'person'
        TERMS = []
        VALUES = []
        UNIQUE = False
        SERIALIZED = True

        # Act
        class AgeIndex(Index):
            name = NAME
            source = SOURCE
            terms = TERMS
            values = VALUES
            unique = UNIQUE
            serialized = SERIALIZED
        age_index = AgeIndex()

        # Assert
        self.assertEqual(age_index.name, NAME)
        self.assertEqual(age_index.source, SOURCE)
        self.assertEqual(age_index.terms, TERMS)
        self.assertEqual(age_index.values, VALUES)
        self.assertEqual(age_index.unique, UNIQUE)
        self.assertEqual(age_index.serialized, SERIALIZED)

    def test_collection(self):
        # Assemble
        NAME = "Jefford"
        EMAIL = "jefford@qwigo.com"
        # Act

        class Person(Collection):
            name = StringField(required=True)
            email = StringField(required=True)

            def __str__(self):
                return self.name
        person = Person(name=NAME, email=EMAIL)
        # Assert
        self.assertEqual(person.name, NAME)
        self.assertEqual(person.email, EMAIL)
        self.assertEqual(str(person), NAME)

    def test_database(self):
        # Assemble
        DATABASE_NAME = "capless-dev"
        NAME = "Jefford"
        EMAIL = "jefford@qwigo.com"

        class Person(Collection):
            name = StringField(required=True)
            email = StringField(required=True)

            def __str__(self):
                return self.name
        # Act
        d = Database(name=DATABASE_NAME)
        d.add_resource(Person)
        d.create()
        d.publish()
        # Assert
        self.assertEqual(d.name, DATABASE_NAME)
        self.assertEqual(d._collection_list[0], Person)

    # def test_pfunkhandler(self):
    #     # Assemble
    #     # Act

    #     pfunk_handler = PFunkHandler({
    #         'default': {
    #             'account_secret_key': 'fnAD9Fi535ACDGe8qq5Z6jHJRFKsQp6WVVQ63uq_',
    #             'database_secret_key': 'fnAD9Fi535ACDGe8qq5Z6jHJRFKsQp6WVVQ63uq_'
    #         }
    #     })

    #     class Person(Collection):
    #         name = StringField(required=True)
    #         email = StringField(required=True)

    #         class Meta:
    #             use_db = 'default'
    #             handler = pfunk_handler
    #             # This should create a simple index in the GraphQL template
    #             default_all_index = True

    #         def __str__(self):
    #             return self.name
    #     # Assert


if __name__ == '__main__':
    unittest.main()

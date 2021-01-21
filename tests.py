import unittest
from envs import env
import random
import string

from pfunk import (Collection, StringField, IntegerField, DateField,
                   DateTimeField, BooleanField, FloatField, PFunkHandler, Database)

def generate_random_string(k=8):
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=k))

class TestPfunk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pfunkhandler = PFunkHandler({
            'db1': {
                'secret': 'fnAD_7N6kLACDbeoz21Cq27_0swR1imUjcknH5Kr'
            }
        })

    @classmethod
    def tearDownClass(cls):
        cls.pfunkhandler = None

    def test_pfunkhandler(self):
        # Assemble
        CONFIG = {'db1': {
            'secret': 'fnAD_7N6kLACDbeoz21Cq27_0swR1imUjcknH5Kr'
        }}
        # Act
        _pfunkhandler = PFunkHandler(CONFIG)

        # Assert
        from faunadb.client import FaunaClient
        self.assertIsInstance(_pfunkhandler['db1']['client'], FaunaClient)
        self.assertIsInstance(_pfunkhandler['db1'], dict)

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

            class Meta:
                handler = self.pfunkhandler['db1']

        person = Person(name=NAME, email=EMAIL)
        person.save()
        # Assert
        self.assertEqual(person.name, NAME)
        self.assertEqual(person.email, EMAIL)
        self.assertEqual(str(person), NAME)

    def test_database(self):
        # Assemble
        NAME = "sample-db"
        # Act
        class MyDB(Database):
            name = NAME
            class Meta:
                handler= self.pfunkhandler['db1']
        mydb = MyDB.create()
        # Assert
        self.assertEqual(mydb.name, NAME)

    def test_database_addresource(self):
        # Assemble
        NAME = generate_random_string()
        # Act
        class MyDB(Database):
            name = NAME
            class Meta:
                handler= self.pfunkhandler['db1']


        mydb = MyDB.create()
        # Assert
        self.assertEqual(mydb.name, NAME)

        class Person(Collection):
            name = StringField(required=True)
            email = StringField(required=True)

            def __str__(self):
                return self.name

            class Meta:
                handler = self.pfunkhandler['db1']




if __name__ == '__main__':
    unittest.main()

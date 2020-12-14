import unittest
from envs import env

from pfunk import Collection, StringField, IntegerField, DateField, DateTimeField, BooleanField, FloatField
from pfunk.indexes import Index
from pfunk.db import Database


class TestPfunk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Database(name='capless-dev')

    @classmethod
    def tearDownClass(cls):
        cls.d = None

    def test_stringfield(self):
        # Assemble
        DEFAULT_VALUE = "Hello World!"
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        # Act
        string_field = StringField(default_value=DEFAULT_VALUE,
                                   required=REQUIRED,
                                   index=INDEX,
                                   index_name=INDEX_NAME,
                                   verbose_name=VERBOSE_NAME
                                   )
        # Assert
        self.assertEqual(string_field.get_graphql_type(), "String")
        self.assertEqual(string_field.default_value, DEFAULT_VALUE)
        self.assertEqual(string_field.required, REQUIRED)
        self.assertEqual(string_field.index, INDEX)
        self.assertEqual(string_field.index_name, INDEX_NAME)
        self.assertEqual(string_field.verbose_name, VERBOSE_NAME)

    def test_integerfield(self):
        # Assemble
        DEFAULT_VALUE = 1
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        # Act
        integer_field = IntegerField(default_value=DEFAULT_VALUE,
                                     required=REQUIRED,
                                     index=INDEX,
                                     index_name=INDEX_NAME,
                                     verbose_name=VERBOSE_NAME
                                     )
        # Assert
        self.assertEqual(integer_field.get_graphql_type(), "Int")
        self.assertEqual(integer_field.default_value, DEFAULT_VALUE)
        self.assertEqual(integer_field.required, REQUIRED)
        self.assertEqual(integer_field.index, INDEX)
        self.assertEqual(integer_field.index_name, INDEX_NAME)
        self.assertEqual(integer_field.verbose_name, VERBOSE_NAME)

    def test_datefield(self):
        # Assemble
        DEFAULT_VALUE = "December 14, 2020"
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        AUTO_NOW = True
        AUTO_NOW_ADD = True
        # Act
        date_field = DateField(default_value=DEFAULT_VALUE,
                               required=REQUIRED,
                               index=INDEX,
                               index_name=INDEX_NAME,
                               verbose_name=VERBOSE_NAME,
                               auto_now=AUTO_NOW,
                               auto_now_add=AUTO_NOW_ADD
                               )
        # Assert
        self.assertEqual(date_field.get_graphql_type(), "Date")
        self.assertEqual(date_field.default_value, DEFAULT_VALUE)
        self.assertEqual(date_field.required, REQUIRED)
        self.assertEqual(date_field.index, INDEX)
        self.assertEqual(date_field.index_name, INDEX_NAME)
        self.assertEqual(date_field.verbose_name, VERBOSE_NAME)
        self.assertEqual(date_field.auto_now, AUTO_NOW)
        self.assertEqual(date_field.auto_now_add, AUTO_NOW_ADD)

    def test_datetimefield(self):
        # Assemble
        DEFAULT_VALUE = "December 14, 2020 8:30 A.M."
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        AUTO_NOW = True
        AUTO_NOW_ADD = True
        # Act
        datetime_field = DateTimeField(default_value=DEFAULT_VALUE,
                                       required=REQUIRED,
                                       index=INDEX,
                                       index_name=INDEX_NAME,
                                       verbose_name=VERBOSE_NAME,
                                       auto_now=AUTO_NOW,
                                       auto_now_add=AUTO_NOW_ADD
                                       )
        # Assert
        self.assertEqual(datetime_field.get_graphql_type(), "Time")
        self.assertEqual(datetime_field.default_value, DEFAULT_VALUE)
        self.assertEqual(datetime_field.required, REQUIRED)
        self.assertEqual(datetime_field.index, INDEX)
        self.assertEqual(datetime_field.index_name, INDEX_NAME)
        self.assertEqual(datetime_field.verbose_name, VERBOSE_NAME)
        self.assertEqual(datetime_field.auto_now, AUTO_NOW)
        self.assertEqual(datetime_field.auto_now_add, AUTO_NOW_ADD)

    def test_booleanfield(self):
        # Assemble
        DEFAULT_VALUE = True
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        # Act
        boolean_field = BooleanField(default_value=DEFAULT_VALUE,
                                     required=REQUIRED,
                                     index=INDEX,
                                     index_name=INDEX_NAME,
                                     verbose_name=VERBOSE_NAME,
                                     )
        # Assert
        self.assertEqual(boolean_field.get_graphql_type(), "Boolean")
        self.assertEqual(boolean_field.default_value, DEFAULT_VALUE)
        self.assertEqual(boolean_field.required, REQUIRED)
        self.assertEqual(boolean_field.index, INDEX)
        self.assertEqual(boolean_field.index_name, INDEX_NAME)
        self.assertEqual(boolean_field.verbose_name, VERBOSE_NAME)

    def test_floatfield(self):
        # Assemble
        DEFAULT_VALUE = 1.0
        REQUIRED = True
        INDEX = False
        INDEX_NAME = "HELLO INDEX"
        VERBOSE_NAME = "HELLO VERBOSE"
        # Act
        float_field = FloatField(default_value=DEFAULT_VALUE,
                                 required=REQUIRED,
                                 index=INDEX,
                                 index_name=INDEX_NAME,
                                 verbose_name=VERBOSE_NAME,
                                 )
        # Assert
        self.assertEqual(float_field.get_graphql_type(), "Float")
        self.assertEqual(float_field.default_value, DEFAULT_VALUE)
        self.assertEqual(float_field.required, REQUIRED)
        self.assertEqual(float_field.index, INDEX)
        self.assertEqual(float_field.index_name, INDEX_NAME)
        self.assertEqual(float_field.verbose_name, VERBOSE_NAME)

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


if __name__ == '__main__':
    unittest.main()

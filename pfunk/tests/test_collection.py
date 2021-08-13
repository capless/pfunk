import unittest

from valley.exceptions import ValidationException

from pfunk.resources import q
from pfunk.tests import Person, Sport, GENDER_PRONOUN


class CollectionTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.collection = Person

    def test_validate_valid(self):
        obj = self.collection(first_name='Mike', last_name='James')
        obj.validate()
        self.assertTrue(obj._is_valid)

    def test_validate_invalid(self):
        obj = self.collection(first_name='Mike')
        with self.assertRaises(ValidationException):
            obj.validate()

    def test_get_fields(self):
        fields = self.collection().get_fields()
        self.assertEqual(fields, {
            'first_name': q.select('first_name', q.var("input")),
            'gender_pronoun': q.select('gender_pronoun', q.var('input')),
            'group': q.select('group', q.var("input")),
            'last_name': q.select('last_name', q.var("input")),
            'sport': q.select('sport', q.var("input"))
        })

    def test_get_collection_name(self):
        self.assertEqual(self.collection().get_collection_name(), 'Person')

    def test_get_enum(self):
        self.assertEqual(self.collection().get_enums(), [GENDER_PRONOUN])

    def test_verbose_plural_name_set(self):
        self.assertEqual(self.collection.get_verbose_plural_name(), 'people')

    def test_verbose_plural_name_unset(self):
        self.assertEqual(Sport.get_verbose_plural_name(), 'sports')

    def test_all_index_name(self):
        self.assertEqual(self.collection().all_index_name(), 'all_people')

    def test_get_unique_together(self):
        sport = Sport()
        sport.get_unique_together()
        self.assertEqual(len(sport.collection_indexes), 1)





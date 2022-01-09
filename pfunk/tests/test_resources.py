import unittest
from pfunk.tests import SimpleIndex
from pfunk.client import q

class IndexTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.index = SimpleIndex()

    def test_get_name(self):
        self.assertEqual(self.index.get_name(), 'simple-index')

    def test_init(self):
        index = SimpleIndex(name='second-index', source='Animal', unique=True)
        self.assertEqual(index.name, 'second-index')
        self.assertEqual(index.source, 'Animal')
        self.assertEqual(index.unique, True)

    def test_get_kwargs(self):
        self.assertEqual(
            self.index.get_kwargs(),
            {
                'name':'simple-index',
                'source': q.collection('Project'),
                'terms': ['name', 'slug'],
                'unique': True
            }
        )
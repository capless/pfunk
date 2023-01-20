import unittest
import os
from unittest import mock
from importlib import reload
import sys

from pfunk.fields import ReferenceField, ManyToManyField

env_vars = {
    'USER_COLLECTION': 'Newuser',
    'GROUP_COLLECTION': 'Newgroup',
    'USER_COLLECTION_DIR': 'pfunk.tests.test_custom_user_group_group_perms.Newuser',
    'GROUP_COLLECTION_DIR': 'pfunk.tests.test_custom_user_group_group_perms.Newgroup'
} 


class TestReloadModule(unittest.TestCase):

    def test_reload_pfunk(self):
        import pfunk
        ug = pfunk.contrib.auth.collections.UserGroups
        for k,v in ug._base_properties.items():
            print(f'K: {k}, V: {dir(v)}\n')
        print(f'')

        # mock.patch.dict(os.environ, env_vars)
        # pfunk = reload(pfunk)
        # # del sys.modules['pfunk']
        # # for x in sys.modules:
        # #     if 'pfunk' in x:
        # #         del x
        # # del pfunk

        
        # ug = pfunk.contrib.auth.collections.UserGroups
        # for k,v in ug._base_properties.items():
        #     print(f'K: {k}, V: {v.get_graphql_type()}\n')
        # print(f'')
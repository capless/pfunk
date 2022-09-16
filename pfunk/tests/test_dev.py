# test_dev.py - a placeholder test for fixing User - Group circular import errors

import os
from valley.utils import import_util

from pfunk.contrib.auth.collections import BaseUser, User
from pfunk.testcase import APITestCase
from pfunk.contrib.auth.collections import Group
from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.fields import EmailField, ManyToManyField, StringField, EnumField


# Simple setup
# Env var setup for user and group
# os.environ['GROUP_COLLECTION'] = 'pfunk.tests.test_dev.NewGroup'
# os.environ['USER_COLLECTION'] = 'pfunk.tests.test_dev.NewUser'

class NewUser(User):
    # groups = ManyToManyField('pfunk.tests.test_dev.NewGroup')
    pass

class NewGroup(Group):
    users = ManyToManyField('pfunk.tests.test_dev.NewUser')

class Blog(Collection):
    """ Collection for DigitalOcean-Type request """
    title = StringField(required=True)
    content = StringField(required=True)
    user = ReferenceField(NewUser)

    def __unicode__(self):
        return self.title

# Test case to see if user-group is working 
class TestUserGroupError(APITestCase):
    collections = [NewUser, NewGroup, Blog]

    def setUp(self) -> None:
        super().setUp()
        self.group = NewGroup.create(name='Power Users', slug='power-users')
        self.user = NewUser.create(username='test', email='tlasso@example.org', first_name='Ted',
                                  last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                  groups=[self.group])
        self.blog = Blog.create(
            title='test_blog', content='test content', user=self.user)

        self.token, self.exp = NewUser.api_login("test", "abc123")
        print(f'\n\nTOKEN: {self.token}')
        print(f'\n\nEXP: {self.exp}')

    def test_mock(self):
        assert True
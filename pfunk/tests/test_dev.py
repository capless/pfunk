# test_dev.py - a placeholder test for fixing User - Group circular import errors

import os
from valley.utils import import_util

from pfunk.contrib.auth.collections import BaseGroup, ExtendedUser
from pfunk.testcase import APITestCase
from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.fields import EmailField, ManyToManyField, StringField, EnumField, ListField


class UserGroups(Collection):
    collection_name = 'custom_users_groups'
    userID = ReferenceField('pfunk.tests.test_dev.Newuser')
    groupID = ReferenceField('pfunk.tests.test_dev.Newgroup')
    permissions = ListField()


class Newgroup(BaseGroup):
    users = ManyToManyField('pfunk.tests.test_dev.Newuser',
                            relation_name='custom_users_groups')


class Newuser(ExtendedUser):
    user_group_class = import_util('pfunk.tests.test_dev.UserGroups')
    group_class = import_util('pfunk.tests.test_dev.Newgroup')
    groups = ManyToManyField(
        'pfunk.tests.test_dev.Newgroup', relation_name='custom_users_groups')
    blogs = ManyToManyField('pfunk.tests.test_dev.Blog',
                            relation_name='users_blogs')


class Blog(Collection):
    title = StringField(required=True)
    content = StringField(required=True)
    users = ManyToManyField('pfunk.tests.test_dev.Newuser',
                            relation_name='users_blogs')

    def __unicode__(self):
        return self.title


# Test case to see if user-group is working
class TestUserGroupError(APITestCase):
    collections = [Newuser, Newgroup, UserGroups, Blog]

    def setUp(self) -> None:
        super().setUp()
        self.group = Newgroup.create(name='Power Users', slug='power-users')
        self.user = Newuser.create(username='test', email='tlasso@example.org', first_name='Ted',
                                   last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                   groups=[self.group])
        self.blog = Blog.create(
            title='test_blog', content='test content', user=self.user, token=self.secret)

        # BUG: logging in returns missing identity
        print(f'TEST USER: {self.user.__dict__}')
        self.token, self.exp = Newuser.api_login("test", "abc123")
        print(f'\n\nTOKEN: {self.token}')
        print(f'\n\nEXP: {self.exp}')

    def test_mock(self):
        assert True

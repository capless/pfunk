# test_dev.py - a placeholder test for fixing User - Group circular import errors

import os
from valley.utils import import_util

from pfunk.contrib.auth.collections import BaseGroup, ExtendedUser, Group, User
from pfunk.testcase import APITestCase
from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.fields import EmailField, ManyToManyField, StringField, EnumField, ListField


class UserGroups(Collection):
    collection_name = 'custom_users_groups'
    userID = ReferenceField('pfunk.tests.test_dev.Newuser')
    groupID = ReferenceField('pfunk.tests.test_dev.Newgroup')
    permissions = ListField()

    def __unicode__(self):
        return f"{self.userID}, {self.groupID}, {self.permissions}"


class Newgroup(BaseGroup):
    users = ManyToManyField('pfunk.tests.test_dev.Newuser',
                            relation_name='custom_users_groups')


class Newuser(ExtendedUser):
    group_class = import_util('pfunk.tests.test_dev.Newgroup')
    groups = ManyToManyField(
        'pfunk.tests.test_dev.Newgroup', relation_name='custom_users_groups')
    # blogs = ManyToManyField('pfunk.tests.test_dev.Blog', relation_name='users_blogs')


class Blog(Collection):
    """ Collection for DigitalOcean-Type request """
    title = StringField(required=True)
    content = StringField(required=True)
    # users = ManyToManyField('pfunk.tests.test_dev.Newuser', relation_name='users_blogs')

    def __unicode__(self):
        return self.title


# Test case to see if user-group is working
class TestUserGroupError(APITestCase):
    collections = [Newuser, Newgroup, Blog]

    def setUp(self) -> None:
        super().setUp()
        self.group = Newgroup.create(name='Power Users', slug='power-users')
        self.user = Newuser.create(username='test', email='tlasso@example.org', first_name='Ted',
                                   last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                   groups=[self.group])
        self.blog = Blog.create(
            title='test_blog', content='test content', user=self.user)

        # BUG: logging in returns wrong credentials error
        print(f'TEST USER: {self.user.__dict__}')
        self.token, self.exp = Newuser.api_login("test", "abc123")
        print(f'\n\nTOKEN: {self.token}')
        print(f'\n\nEXP: {self.exp}')

    def test_mock(self):
        assert True

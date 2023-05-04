# test_dev.py - a placeholder test for fixing User - Group circular import errors

import os
from valley.utils import import_util

from pfunk.contrib.auth.collections import BaseGroup, ExtendedUser, BaseUserGroup as ug
from pfunk.testcase import APITestCase
from pfunk import Collection, StringField, ReferenceField, ManyToManyField
from pfunk.fields import ManyToManyField, StringField
from pfunk.contrib.auth.resources import GenericUserBasedRoleM2M


class UserGroups(ug):
    userID = ReferenceField(
        'pfunk.tests.test_web_custom_user_group_m2m.Newuser')
    groupID = ReferenceField(
        'pfunk.tests.test_web_custom_user_group_m2m.Newgroup')


class Newgroup(BaseGroup):
    users = ManyToManyField('pfunk.tests.test_web_custom_user_group_m2m.Newuser',
                            relation_name='custom_users_groups')


class Newuser(ExtendedUser):
    group_collection = 'Newgroup'
    user_group_class = import_util(
        'pfunk.tests.test_web_custom_user_group_m2m.UserGroups')
    group_class = import_util(
        'pfunk.tests.test_web_custom_user_group_m2m.Newgroup')
    groups = ManyToManyField(
        'pfunk.tests.test_web_custom_user_group_m2m.Newgroup', relation_name='custom_users_groups')
    blogs = ManyToManyField('pfunk.tests.test_web_custom_user_group_m2m.Blog',
                            relation_name='users_blogs')


class Blog(Collection):
    user_collection = 'Newuser'
    group_collection = 'Newgroup'
    user_collection_dir = 'pfunk.tests.test_web_custom_user_group_m2m.Newuser'
    group_collection_dir = 'pfunk.tests.test_web_custom_user_group_m2m.Newgroup'
    collection_roles = [GenericUserBasedRoleM2M]
    title = StringField(required=True)
    content = StringField(required=True)
    users = ManyToManyField('pfunk.tests.test_web_custom_user_group_m2m.Newuser',
                            relation_name='users_blogs')

    def __unicode__(self):
        return self.title


# Test case to see if user-group is working
class TestCustomUserM2M(APITestCase):
    collections = [Newuser, Newgroup, UserGroups, Blog]

    def setUp(self) -> None:
        super().setUp()
        self.group = Newgroup.create(name='Power Users', slug='power-users')
        self.user = Newuser.create(username='test', email='tlasso@example.org', first_name='Ted',
                                   last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                   groups=[self.group])
        self.user2 = Newuser.create(username='test2', email='tlasso2@example.org', first_name='Juliuz',
                                    last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                    groups=[self.group])
        self.blog = Blog.create(
            title='test_blog', content='test content', users=[self.user], token=self.secret)
        self.token, self.exp = Newuser.api_login("test", "abc123")

    def test_read(self):
        res = self.c.get(f'/json/blog/detail/{self.blog.ref.id()}/',
                         headers={
                             "Authorization": self.token})
        self.assertTrue(res.status_code, 200)
        self.assertEqual("test_blog", res.json['data']['data']['title'])

    def test_read_all(self):
        res = self.c.get(f'/json/blog/list/',
                         headers={
                             "Authorization": self.token})
        self.assertTrue(res.status_code, 200)

    def test_create(self):
        self.assertNotIn("new blog", [
            blog.title for blog in Blog.all()])
        res = self.c.post('/json/blog/create/',
                          json={
                              "title": "new blog",
                              "content": "I created a new blog.",
                              "users": [self.user.ref.id(), self.user2.ref.id()]},
                          headers={
                              "Authorization": self.token})

        self.assertTrue(res.status_code, 200)
        self.assertIn("new blog", [
            blog.title for blog in Blog.all()])

    def test_update(self):
        self.assertNotIn("updated blog", [
            blog.title for blog in Blog.all()])
        res = self.c.put(f'/json/blog/update/{self.blog.ref.id()}/',
                         json={
                             "title": "updated blog",
                             "content": "I updated my blog.",
                             "users": [self.user.ref.id()]
                         },
                         headers={
                             "Authorization": self.token})

        self.assertTrue(res.status_code, 200)
        self.assertIn("updated blog", [
            blog.title for blog in Blog.all()])

    def test_delete(self):
        res = self.c.delete(f'/json/blog/delete/{self.blog.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })

        self.assertTrue(res.status_code, 200)
        self.assertNotIn("test_blog", [
            blog.title for blog in Blog.all()])

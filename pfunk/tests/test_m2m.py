# test_dev.py - a placeholder test for fixing User - Group circular import errors

import os
from valley.utils import import_util
from pprint import pprint as p

from pfunk.contrib.auth.collections import BaseGroup, ExtendedUser, UserGroups
from pfunk.testcase import APITestCase
from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.fields import EmailField, ManyToManyField, StringField, EnumField, ListField
from pfunk.contrib.auth.resources import GenericGroupBasedRole, GenericUserBasedRole, GenericUserBasedRoleM2M


class Newgroup(BaseGroup):
    users = ManyToManyField('pfunk.tests.test_m2m.Newuser',
                            relation_name='custom_users_groups')


class Newuser(ExtendedUser):
    user_group_class = import_util('pfunk.tests.test_m2m.UserGroups')
    group_class = import_util('pfunk.tests.test_m2m.Newgroup')
    groups = ManyToManyField(
        'pfunk.tests.test_m2m.Newgroup', relation_name='custom_users_groups')
    blogs = ManyToManyField('pfunk.tests.test_m2m.Blog',
                            relation_name='users_blogs')


class Blog(Collection):
    collection_roles = [GenericUserBasedRoleM2M]
    title = StringField(required=True)
    content = StringField(required=True)
    users = ManyToManyField('pfunk.tests.test_m2m.Newuser',
                          relation_name='users_blogs')

    def __unicode__(self):
        return self.title


# Test case to see if user-group is working
class TestCustomUserM2M(APITestCase):
    collections = [Newuser, Newgroup, UserGroups, Blog]

    def setUp(self) -> None:
        os.environ['USER_COLLECTION'] = 'Newuser'
        os.environ['GROUP_COLLECTION'] = 'Newgroup'
        os.environ['USER_COLLECTION_DIR'] = 'pfunk.tests.test_m2m.Newuser'
        os.environ['GROUP_COLLECTION_DIR'] = 'pfunk.tests.test_m2m.Newgroup'
        super().setUp()
        self.group = Newgroup.create(name='Power Users', slug='power-users')
        self.user = Newuser.create(username='test', email='tlasso@example.org', first_name='Ted',
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
                              "user": self.user.ref.id()},
                          headers={
                              "Authorization": self.token})

        self.assertTrue(res.status_code, 200)
        self.assertIn("new blog", [
            blog.title for blog in Blog.all()])

    # def test_update(self):
    #     self.assertNotIn("the updated street somewhere", [
    #         house.address for house in Blog.all()])
    #     res = self.c.put(f'/json/blog/update/{self.blog.ref.id()}/',
    #                      json={
    #                          "title": "updated blog",
    #                          "content": "I updated my blog.",
    #                          "user": self.user.ref.id()},
    #                      headers={
    #                          "Authorization": self.token})

    #     print(f'\n\nRESPONSE: {res.json}\n\n')
    #     self.assertTrue(res.status_code, 200)
    #     self.assertIn("updated blog", [
    #         blog.title for blog in Blog.all()])

    def test_delete(self):
        res = self.c.delete(f'/json/blog/delete/{self.blog.ref.id()}/',
                            headers={
                                "Authorization": self.token,
                                "Content-Type": "application/json"
                            })

        self.assertTrue(res.status_code, 200)

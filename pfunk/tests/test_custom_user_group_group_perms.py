from valley.utils import import_util

from pfunk.contrib.auth.key import PermissionGroup
from pfunk.testcase import APITestCase
from pfunk.contrib.auth.collections import BaseGroup, ExtendedUser, BaseUserGroup as ug
from pfunk import Collection, StringField, ReferenceField, ManyToManyField
from pfunk.fields import ManyToManyField, StringField
from pfunk.contrib.auth.resources import GenericGroupBasedRole


class UserGroups(ug):
    userID = ReferenceField('pfunk.tests.test_custom_user_group_group_perms.Newuser')
    groupID = ReferenceField('pfunk.tests.test_custom_user_group_group_perms.Newgroup')


class Newgroup(BaseGroup):
    users = ManyToManyField('pfunk.tests.test_custom_user_group_group_perms.Newuser',
                            relation_name='custom_users_groups')


class Blog(Collection):
    user_collection = 'Newuser'
    group_collection = 'Newgroup'
    user_collection_dir = 'pfunk.tests.test_custom_user_group_group_perms.Newuser'
    group_collection_dir = 'pfunk.tests.test_custom_user_group_group_perms.Newgroup'
    collection_roles = [GenericGroupBasedRole]
    title = StringField(required=True)
    content = StringField(required=True)
    group = ReferenceField('pfunk.tests.test_custom_user_group_group_perms.Newgroup',
                           relation_name='newgroup_blogs')

    def __unicode__(self):
        return self.title


class Newuser(ExtendedUser):
    group_collection = 'Newgroup'
    user_group_class = import_util('pfunk.tests.test_custom_user_group_group_perms.UserGroups')
    group_class = import_util('pfunk.tests.test_custom_user_group_group_perms.Newgroup')
    groups = ManyToManyField(
        'pfunk.tests.test_custom_user_group_group_perms.Newgroup', relation_name='custom_users_groups')


class TestCustomGroupBasedPerms(APITestCase):
    collections = [Newuser, Newgroup, Blog, UserGroups]

    def setUp(self) -> None:
        super().setUp()
        self.group = Newgroup.create(name='Power Users', slug='power-users')
        self.user = Newuser.create(username='test_user', email='tlasso@example.org', first_name='Ted',
                                   last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                   groups=[self.group])
        perms = self.user.add_permissions(
            self.group, [PermissionGroup(Blog, ['create', 'read', 'write', 'delete'])])
        self.token, self.exp = Newuser.api_login("test_user", "abc123")
        self.raw_token = Newuser.login("test_user", "abc123")
        self.blog = Blog.create(
            title='test_blog', content='test content', group=self.group)

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
                              "group": self.group.ref.id()},
                          headers={
                              "Authorization": self.token})
        self.assertTrue(res.status_code, 200)
        self.assertIn("new blog", [
            blog.title for blog in Blog.all()])

    def test_update(self):
        self.assertNotIn("the updated street somewhere", [
            house.address for house in Blog.all()])
        res = self.c.put(f'/json/blog/update/{self.blog.ref.id()}/',
                         json={
                              "title": "updated blog",
                              "content": "I updated my blog."},
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

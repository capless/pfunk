import os
from valley.utils import import_util

from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.testcase import APITestCase
from pfunk.web.request import DigitalOCeanRequest
from pfunk.web.views.json import DetailView, CreateView, UpdateView, DeleteView, ListView
from pfunk.contrib.auth.views import ForgotPasswordChangeView, LoginView, SignUpView, VerifyEmailView, LogoutView, UpdatePasswordView, ForgotPasswordView
from pfunk.tests.init_digitalocean import DOUser, DOGroup, Blog


# TODO: Mock digitalocean environment functions here to emulate working proj in digitalocean ecosystem
# TODO: find a way to override requestclass for the whole pfunk app
class TestWebDigitalOcean(APITestCase):
    collections = [DOUser, DOGroup, Blog]

    def setUp(self) -> None:
        super().setUp()
        self.group = DOGroup.create(name='Power Users', slug='power-users')
        self.user = DOUser.create(username='test', email='tlasso@example.org', first_name='Ted',
                                  last_name='Lasso', _credentials='abc123', account_status='ACTIVE',
                                  groups=[self.group])
        self.blog = Blog.create(
            title='test_blog', content='test content', user=self.user)

        self.token, self.exp = DOUser.api_login("test", "abc123")
        print(f'\n\nTOKEN: {self.token}')
        print(f'\n\nEXP: {self.exp}')

    def test_mock(self):
        assert True

    # def test_read(self):
    #     res = self.c.get(f'/blog/detail/{self.blog.ref.id()}/',
    #                      headers={
    #                          "Authorization": self.token})
    #     print(f'RESPONSE:\n{res.json}')
    #     self.assertTrue(res.json['success'])
    #     self.assertEqual("test content", res.json['data']['data']['content'])

    # def test_read_all(self):
    #     res = self.c.get(f'/blog/list/',
    #                      headers={
    #                          "Authorization": self.token})
    #     self.assertTrue(res.json['success'])

    # def test_create(self):
    #     self.assertNotIn("the created blog", [
    #         blog.content for blog in Blog.all()])
    #     res = self.c.post('/blog/create/',
    #                       json={
    #                           "title": "test_create_blog",
    #                           "content": "the created blog",
    #                           "user": self.user.ref.id()},
    #                       headers={
    #                           "Authorization": self.token})

    #     self.assertTrue(res.json['success'])
    #     self.assertIn("test_create_blog", [
    #                   blog.title for blog in Blog.all()])

    # def test_update(self):
    #     self.assertNotIn("the updated blog", [
    #         house.address for house in Blog.all()])
    #     res = self.c.put(f'/blog/update/{self.blog.ref.id()}/',
    #                      json={
    #                          "title": "test_updated_blog",
    #                          "content": "the updated blog",
    #                          "user": self.user.ref.id()},
    #                      headers={
    #                          "Authorization": self.token})

    #     self.assertTrue(res.json['success'])
    #     self.assertIn("test_updated_blog", [
    #                   blog.title for blog in Blog.all()])

    # def test_delete(self):
    #     res = self.c.delete(f'/blog/delete/{self.blog.ref.id()}/',
    #                         headers={
    #                             "Authorization": self.token,
    #                             "Content-Type": "application/json"
    #                         })

    #     self.assertTrue(res.json['success'])

import os
from valley.utils import import_util

from pfunk.contrib.auth.collections.user import BaseUser, User
from pfunk.contrib.auth.collections.group import Group
from pfunk import Collection, StringField, EnumField, Enum, ReferenceField, SlugField, ManyToManyField, IntegerField, BooleanField, DateTimeField
from pfunk.web.request import DigitalOCeanRequest


class DOLoginView(LoginView):
    request_class = DigitalOCeanRequest


class DOSignUpView(SignUpView):
    request_class = DigitalOCeanRequest


class DOVerifyEmailView(VerifyEmailView):
    request_class = DigitalOCeanRequest


class DOLogoutView(LogoutView):
    request_class = DigitalOCeanRequest


class DOUpdatePasswordView(UpdatePasswordView):
    request_class = DigitalOCeanRequest


class DOForgotPasswordView(ForgotPasswordView):
    request_class = DigitalOCeanRequest


class DOForgotPasswordChangeView(ForgotPasswordChangeView):
    request_class = DigitalOCeanRequest


class DOUser(User):
    collection_views = [DOLoginView, DOSignUpView, DOVerifyEmailView, DOLogoutView,
                        DOUpdatePasswordView, DOForgotPasswordView, DOForgotPasswordChangeView]
    group_class = import_util('pfunk.tests.init_digitalocean.DOGroup')

class DOGroup(Group):
    pass


class DODetailView(DetailView):
    request_class = DigitalOCeanRequest


class DOCreateView(CreateView):
    request_class = DigitalOCeanRequest


class DOUpdateView(UpdateView):
    request_class = DigitalOCeanRequest


class DOListView(ListView):
    request_class = DigitalOCeanRequest


class DODeleteView(DeleteView):
    request_class = DigitalOCeanRequest


class Blog(Collection):
    """ Collection for DigitalOcean-Type request """
    title = StringField(required=True)
    content = StringField(required=True)
    user = ReferenceField(DOUser)
    crud_views = [DODetailView, DOCreateView,
                  DOUpdateView, DOListView, DODeleteView]

    def __unicode__(self):
        return self.title
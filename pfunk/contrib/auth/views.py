from abc import ABC

from envs import env
from werkzeug.routing import Rule

from pfunk.web.views.base import ActionMixin
from pfunk.web.views.json import JSONView


class JSONAuthView(JSONView, ABC):
    http_methods = ['post']

    def get_query_kwargs(self):
        return self.request.get_json()


class LoginView(ActionMixin, JSONAuthView):
    action = 'login'
    login_required = False

    def get_query(self):
        token, exp = self.collection.api_login(**self.get_query_kwargs())
        self.set_cookie(env('TOKEN_COOKIE_NAME', 'tk'), value=token, max_age=exp.timestamp())
        return {
            'token': token,
            'exp': exp
        }


class LogoutView(ActionMixin, JSONAuthView):
    action = 'logout'
    login_required = True

    def get_query(self):
        self.collection.logout(_token=self.request.token)


class SignUpView(ActionMixin, JSONAuthView):
    action = 'sign-up'
    login_required = False

    def get_query(self):
        return self.collection.signup(**self.get_query_kwargs())


class VerifyEmailView(ActionMixin, JSONAuthView):
    action = 'verify'
    login_required = False
    http_methods = ['get']

    def get_query(self):
        return self.collection.verify_email(str(self.request.kwargs.get('verification_key')))

    @classmethod
    def url(cls, collection):
        return Rule(f'/{collection.get_class_name()}/{cls.action}/<uuid:verification_key>/',
                    endpoint=cls.as_view(collection),
                    methods=cls.http_methods)


class ForgotPasswordView(JSONAuthView):
    login_required = False

    def get_query(self):
        return self.collection.forgot_passsword(**self.get_query_kwargs())


class WebhookView(JSONView):
    pass



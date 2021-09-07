from abc import ABC

from envs import env

from pfunk.web.views.base import ActionMixin
from pfunk.web.views.json import JSONView


class JSONAuthView(JSONView, ABC):
    http_methods = ['post']

    def get_query_kwargs(self):
        return self.request.get_json()


class LoginView(ActionMixin, JSONAuthView):
    action = 'login'

    def get_query(self):
        token, exp = self.collection.api_login(**self.get_query_kwargs())
        self.set_cookie(env('TOKEN_COOKIE_NAME', 'tk'), value=token, max_age=exp.timestamp())
        return {
            'token': token,
            'exp': exp
        }


class SignUpView(ActionMixin, JSONAuthView):
    action = 'sign-up'

    def get_query(self):
        return self.collection.signup(**self.get_query_kwargs())


class ForgotPasswordView(JSONAuthView):

    def get_query(self):
        return self.collection.forgot_passsword(**self.get_query_kwargs())


class WebhookView(JSONView):
    pass



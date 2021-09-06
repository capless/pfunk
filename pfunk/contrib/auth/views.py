from abc import ABC

from pfunk.web.views.json import JSONView


class JSONAuthView(JSONView, ABC):

    def get_query_kwargs(self):
        return self.request.get_json()


class LoginView(JSONAuthView):
    http_methods = ['post']

    def get_query(self):
        return self.collection.login(**self.get_query_kwargs())


class SignUpView(JSONAuthView):

    def get_query(self):
        return self.collection.signup(**self.get_query_kwargs())


class ForgotPasswordView(JSONAuthView):

    def get_query(self):
        return self.collection.forgot_passsword(**self.get_query_kwargs())


class WebhookView(JSONView):
    pass



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
    """ Creates a login view to enable user login

    Sets the token in the cookie after successful
    operation in addition to returning the token
    value itself

    Returns:
        auth_token (dict):
            token (str): auth token of the user
            exp (str): expiration of the token  
    """
    action = 'login'
    login_required = False

    def get_query(self):
        token, exp = self.collection.api_login(**self.get_query_kwargs())
        self.set_cookie(env('TOKEN_COOKIE_NAME', 'tk'),
                        value=token, max_age=exp.timestamp())
        return {
            'token': token,
            'exp': exp
        }

    def _payload_docs(self):
        return {"data": [
            {
                "name": "username",
                "in": "formData",
                "description": "Username of the user",
                "required": True,
                "type": "string"
            },
            {
                "name": "password",
                "in": "formData",
                "description": "Password of the user",
                "required": True,
                "type":"string",
                "format": "password"
            }
        ]}


class LogoutView(ActionMixin, JSONAuthView):
    """ Creates a logout view to enable logout via endpoint 
    
    Invalidates the token and removes the cookie
    """
    action = 'logout'
    login_required = True

    def get_query(self):
        self.collection.logout(_token=self.request.token)
        self.delete_cookie(env('TOKEN_COOKIE_NAME', 'tk'))


class SignUpView(ActionMixin, JSONAuthView):
    """ Creates a signup view to enable signing up of users 
    
    This will create an inactive user that needs to be
    activated by following the email verification instructions
    """
    action = 'sign-up'
    login_required = False

    def get_query(self):
        return self.collection.signup(**self.get_query_kwargs())

    def _payload_docs(self):
        return {"data": [
            {
                "name": "username",
                "in": "formData",
                "description": "username of the user",
                "required": True,
                "type": "string"
            },
            {
                "name": "password",
                "in": "formData",
                "description": "password of the user",
                "required": True,
                "type":"string",
                "format": "password"
            }
        ]}

class VerifyEmailView(ActionMixin, JSONAuthView):
    """ Creates a view that enables verification of a user 
    
    Activates the user from the given verification key
    """
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


class UpdatePasswordView(ActionMixin, JSONAuthView):
    """ Create a view that allows user to update their password  
        with the use of current password
    """
    action = 'update-password'
    login_required = True
    http_methods = ['post']

    def get_query(self):
        kwargs = self.get_query_kwargs()
        self.collection.update_password(kwargs['current_password'], kwargs['new_password'],
                                        kwargs['new_password_confirm'], _token=self.request.token)

    def _payload_docs(self):
            return {"data": [
                {
                    "name": "current_password",
                    "in": "formData",
                    "description": "current password of the user",
                    "required": True,
                    "type": "string",
                    "format": "password"
                },
                {
                    "name": "new_password",
                    "in": "formData",
                    "description": "new password of the user",
                    "required": True,
                    "type":"string",
                    "format": "password"
                },
                {
                    "name": "new_password_confirm",
                    "in": "formData",
                    "description": "confirm the new password of the user by entering the same string",
                    "required": True,
                    "type":"string",
                    "format": "password"
                }
            ]}

class ForgotPasswordView(ActionMixin, JSONAuthView):
    """ Create a view to allow call of forgot password func """
    action = 'forgot-password'
    login_required = False
    http_methods = ['post']

    def get_query(self):
        return self.collection.forgot_password(**self.get_query_kwargs())
    
    def _payload_docs(self):
            return {"data": [
                {
                    "name": "email",
                    "in": "formData",
                    "description": "email of the user",
                    "required": True,
                    "type": "string"
                }
            ]}


class ForgotPasswordChangeView(ActionMixin, JSONAuthView):
    """
    Accepts a hashed key from the forgot-password email, validates
    it if it matches the user's and change the password
    """
    action = 'forgot-password'
    login_required = False
    http_methods = ['put']

    def get_query(self):
        kwargs = self.get_query_kwargs()
        return self.collection.verify_email(
            str(kwargs['verification_key']),
            verify_type='forgot',
            password=kwargs['password'])

    def _payload_docs(self):
            return {"data": [
                {
                    "name": "verification_key",
                    "in": "formData",
                    "description": "hashed key for verification of forgot password event",
                    "required": True,
                    "type": "string"
                }
            ]}

class WebhookView(JSONView):
    pass

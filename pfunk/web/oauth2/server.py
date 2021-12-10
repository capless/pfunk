from authlib.oauth2.rfc6749.authorization_server import AuthorizationServer as _AuthorizationServer
from authlib.oauth2.rfc6749.authenticate_client import ClientAuthentication
from authlib.oauth2.rfc6750 import BearerTokenGenerator
from authlib.common.security import generate_token as _generate_token
from envs import env
import importlib

from pfunk.web.oauth2.token import access_token_generator as _access_token_generator
from pfunk.web.oauth2.token import refresh_token_generator as _refresh_token_generator
from pfunk.web.oauth2.token import TOKEN_EXPIRES_IN
from pfunk.web.request import HTTPRequest, OAuth2Request
from pfunk.web.oauth2.util import create_oauth_request
from pfunk.web.response import Response


# TODO: Test if request-response implementation is working
# TODO: Decide whether token generators are needed just like the implementation in django AuthServer
# NOTE: The functions that does not need overriding was removed already
# NOTE: All of docstrings are directly acquired from authlib framework. ONLY REWORK DOCS AFTER IT ACTUALLY WORKS
class AuthorizationServer(_AuthorizationServer):
    """Authorization server that handles Authorization Endpoint and Token
    Endpoint. 

    This server accepts (and returns) own-implemented of `request` objects, that way, 
    it can be integrated well with specific objectives. 

    :param scopes_supported: A list of supported scopes by this authorization server.
    """

    def __init__(self, client_model, token_model, scopes_supported=None):
        self.client_model = client_model
        self.token_model = token_model
        self.scopes_supported = scopes_supported
        self._token_generators = {}
        self._client_auth = None
        self._authorization_grants = []
        self._token_grants = []
        self._endpoints = {}

    def query_client(self, client_id):
        """Query OAuth client by client_id. The client model class MUST
        implement the methods described by
        :class:`~authlib.oauth2.rfc6749.ClientMixin`.
        """
        return self.client_model.get(client_id)

    def save_token(self, token, request):
        """Define function to save the generated token into database."""
        client = request.client
        if request.user:
            user_id = request.user
        else:
            user_id = client.user
        token = self.token_model.save(
            client_id=client.client_id,
            user=user_id,
            **token
        )
        return token

    def register_client_auth_method(self, method, func):
        """Add more client auth method. The default methods are:

        * none: The client is a public client and does not have a client secret
        * client_secret_post: The client uses the HTTP POST parameters
        * client_secret_basic: The client uses HTTP Basic

        :param method: Name of the Auth method
        :param func: Function to authenticate the client

        The auth method accept two parameters: ``query_client`` and ``request``,
        an example for this method::

            def authenticate_client_via_custom(query_client, request):
                client_id = request.headers['X-Client-Id']
                client = query_client(client_id)
                do_some_validation(client)
                return client

            authorization_server.register_client_auth_method(
                'custom', authenticate_client_via_custom)
        """
        if self._client_auth is None and self.query_client:
            self._client_auth = ClientAuthentication(self.query_client)

        self._client_auth.register(method, func)

    def get_error_uri(self, request, error):
        """Return a URI for the given error, framework may implement this method."""
        return None

    def create_oauth2_request(self, request):
        """This method MUST be implemented in framework integrations. It is
        used to create an OAuth2Request instance.

        :param request: the "request" instance in framework
        :return: OAuth2Request instance
        """
        return create_oauth_request(request, OAuth2Request)

    def create_json_request(self, request):
        """This method MUST be implemented in framework integrations. It is
        used to create an HttpRequest instance.

        :param request: the "request" instance in framework
        :return: HttpRequest instance
        """
        req = create_oauth_request(request, HTTPRequest, True)
        req.user = request.user
        return req

    def handle_response(self, status, body, headers):
        """Return HTTP response. Framework MUST implement this function."""
        resp = Response(payload=body, headers=headers)
        if status:
            resp.status_code = status
        return resp

    def create_bearer_token_generator(self, use_default=True):
        """Default method to create BearerToken generator."""
        conf = _access_token_generator() if use_default else True
        access_token_generator = create_token_generator(conf, 42)

        conf = _refresh_token_generator() if use_default else True
        refresh_token_generator = create_token_generator(conf, 48)

        conf = TOKEN_EXPIRES_IN
        expires_generator = create_token_expires_in_generator(conf)

        return BearerTokenGenerator(
            access_token_generator=access_token_generator,
            refresh_token_generator=refresh_token_generator,
            expires_generator=expires_generator,
        )


def create_token_generator(token_generator_conf, length=42):
    if callable(token_generator_conf):
        return token_generator_conf

    if isinstance(token_generator_conf, str):
        return importlib.import_module(token_generator_conf)
    elif token_generator_conf is True:
        def token_generator(*args, **kwargs):
            return _generate_token(length)
        return token_generator


def create_token_expires_in_generator(expires_in_conf=None):
    data = {}
    data.update(BearerTokenGenerator.GRANT_TYPES_EXPIRES_IN)
    if expires_in_conf:
        data.update(expires_in_conf)

    def expires_in(client, grant_type):
        return data.get(grant_type, BearerTokenGenerator.DEFAULT_EXPIRES_IN)

    return expires_in

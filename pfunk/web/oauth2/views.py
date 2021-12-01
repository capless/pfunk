from authlib.oauth2.rfc6749 import grants
from authlib.common.security import generate_token

from pfunk.web.oauth2.models import OAuth2Client, OAuth2Token, AuthorizationCode
from pfunk.web.views.base import View
from pfunk.exceptions import DocNotFound
from pfunk.web.oauth2.server import AuthorizationServer

# TODO: Determine if using the generic `AuthorizationServer`` is more flexible than Django implementation
server = AuthorizationServer(OAuth2Client, OAuth2Token)

# use ``server.create_authorization_response`` to handle authorization endpoint


class OAuthAuthorize(View):
    """ Authorization Server for user to allow access to 3rd-party app """

    def get(self, **kwargs):
        """ Should be overridden to enable use of HTML for
            the user to allow access

            Upon initial request, the view should return a
            form that will give the user choice to allow
            the access. The second request should accept
            the form value and if it was allowed, return
            `server.create_authorization_response`
        """
        raise NotImplementedError
        # grant = server.get_consent_grant(
        #     self.request, end_user=self.request.user)
        # client = grant.client
        # scope = client.get_allowed_scope(grant.request.scope)
        # context = dict(grant=grant, client=client,
        #                scope=scope, user=self.request.user)

        # return render(self.request, 'authorize.html', context)

        # if is_user_confirmed(request):
        #     return server.create_authorization_response(self.request, grant_user=request.user)

        # return server.create_authorization_response(self.request, grant_user=None)

    def post(self, **kwargs):
        """ Return an OAuth token """
        return server.create_token_response(self.request)


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant, View):
    """ OAuth2 Authorization Code grant views for acquiring Access Token """

    def save_authorization_code(self, code, request):
        """ Create Authorization code """
        client = request.client
        auth_code = AuthorizationCode.create(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            response_type=request.response_type,
            scope=request.scope,
            user=request.user,
        )

        return auth_code

    def query_authorization_code(self, code, client):
        """ Query auth code using the `code` & `client_id` """
        try:
            # TODO: Before this query, an index should be created too
            item = AuthorizationCode.get_by(
                'auth_code_by_code',
                terms=[code, client.client_id]
            )
        except DocNotFound:
            return None

        if not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        """ Delete the given auth code """
        authorization_code.delete()

    def authenticate_user(self, authorization_code):
        """ Return the `User` that is associated with the auth code """
        return authorization_code.user


# TODO: See if pfunk token will work better than migrating to this
class RevokeToken(View):
    """ View for revoking the last access/refresh token """

    def post(self, **kwargs):
        pass


class IntrospectToken(View):
    """ View for knowing the token's content """

    def query_token(self, token, token_type_hint):
        """ Query the token in the db and return it
        
        Args:
            token (`pfunk.web.oauth2.models.OAuthToken`, required):
                The token object that holds token contents
            token_type_hint (str, required):
                The type of the token `['access_token', 'refresh_token']`

        Returns:
            token (`pfunk.web.oauth2.models.OAuthToken'):
                The token model acquired from db
        """
        pass

    def introspect_token(self, token):
        """ Return the contents of the token """
        # return {
        #     'active': True,
        #     'client_id': token.client_id,
        #     'token_type': token.token_type,
        #     'username': get_token_username(token),
        #     'scope': token.get_scope(),
        #     'sub': get_token_user_sub(token),
        #     'aud': token.client_id,
        #     'iss': 'https://server.example.com/',
        #     'exp': token.expires_at,
        #     'iat': token.issued_at,
        # }
        pass

    def check_permission(self, token, client, request):
        # TODO: Determine what should be the factor of permissions, whether from Fauna roles or endpoint

        # for example, we only allow internal client to access introspection endpoint
        # return client.client_type == 'internal'
        pass

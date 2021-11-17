from authlib.integrations.django_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import grants
from authlib.common.security import generate_token

from pfunk.web.oauth2.models import OAuth2Client, OAuth2Token, AuthorizationCode
from pfunk.web.views.base import View
from pfunk.exceptions import DocNotFound

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
        grant = server.get_consent_grant(
            self.request, end_user=self.request.user)
        client = grant.client
        scope = client.get_allowed_scope(grant.request.scope)
        context = dict(grant=grant, client=client,
                       scope=scope, user=self.request.user)

        # TODO: (SEE FIRST IF RENDERING HTML IS ONE OF THE PLANS IN PFUNK OR IF IT IS EVER NEEDED AT ALL)
        # TODO: Render an HTML
        return render(self.request, 'authorize.html', context)

        # TODO: After receiving of form is the user confirmed, return the response
        if is_user_confirmed(request):
            return server.create_authorization_response(self.request, grant_user=request.user)

        return server.create_authorization_response(self.request, grant_user=None)

    def post(self, **kwargs):
        """ Return an OAuth token """
        return server.create_token_response(self.request)


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """ OAuth2 Authorization Code grant views """

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

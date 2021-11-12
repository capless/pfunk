from authlib.integrations.django_oauth2 import AuthorizationServer

from pfunk.web.oauth2.models import OAuth2Client, OAuth2Token
from pfunk.web.views.base import View

server = AuthorizationServer(OAuth2Client, OAuth2Token)

# use ``server.create_authorization_response`` to handle authorization endpoint


class OAuthAuthorize(View):
    """ Authorization Server for user to allow access to 3rd-party"""

    def get(self, **kwargs):
        grant = server.get_consent_grant(self.request, end_user=request.user)
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
        return server.create_token_response(self.request)

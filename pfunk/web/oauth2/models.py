from authlib.oauth2.rfc6749 import ClientMixin, TokenMixin, AuthorizationCodeMixin
from authlib.oauth2.util import scope_to_list, list_to_scope

from pfunk.fields import StringField, IntegerField, DateTimeField, ReferenceField, BooleanField
from pfunk.collection import Collection
from pfunk.contrib.auth.collections import User as PFunkUser
from pfunk.web.oauth2.util import now_timestamp


class OAuth2Client(Collection, ClientMixin):
    """ Model for registering `Clients` to allow connection """
    user = ReferenceField(PFunkUser)
    client_id = StringField(unique=True)
    client_secret = StringField()
    client_name = StringField()
    redirect_uris = StringField()
    default_redirect_uri = StringField()
    scope = StringField()
    response_type = StringField()
    grant_type = StringField()
    token_endpoint_auth_method = StringField()

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.default_redirect_uri

    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        allowed = set(scope_to_list(self.scope))
        return list_to_scope([s for s in scope.split() if s in allowed])

    def check_redirect_uri(self, redirect_uri):
        if redirect_uri == self.default_redirect_uri:
            return True
        return redirect_uri in self.redirect_uris

    def has_client_secret(self):
        return bool(self.client_secret)

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == 'token':
            return self.token_endpoint_auth_method == method
        # TODO: developers can update this check method
        return True

    def check_response_type(self, response_type):
        allowed = self.response_type.split()
        return response_type in allowed

    def check_grant_type(self, grant_type):
        allowed = self.grant_type.split()
        return grant_type in allowed


class OAuth2Token(Collection, TokenMixin):
    """ Token class collection """
    user = ReferenceField(PFunkUser)
    client_id = StringField(required=True)
    token_type = StringField(required=True)
    access_token = StringField(required=True, unique=True)
    refresh_token = StringField(max_length=255)
    scope = StringField(default='')
    revoked = BooleanField(default=False)
    issued_at = IntegerField(null=False, default=now_timestamp)
    expires_in = IntegerField(null=False, default=0)

    def get_client_id(self):
        return self.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in


# TODO: Create `AuthorizationCode` model
class AuthorizationCode(Collection, AuthorizationCodeMixin):
    pass

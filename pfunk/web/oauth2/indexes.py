from pfunk.resources import Index
from pfunk.web.oauth2.models import OAuth2Client, OAuth2Token, AuthorizationCode


class AuthCodeByCode(Index):
    name = "auth_code_by_code"
    source = AuthorizationCode.__name__
    terms = ['code']


class TokenByAccessToken(Index):
    name = "oauth2_token_by_access_token"
    source = OAuth2Token.__name__
    terms = ['access_token']


class TokenByRefreshToken(Index):
    name = "oauth2_token_by_refresh_token"
    source = OAuth2Token.__name__
    terms = ['refresh_token']

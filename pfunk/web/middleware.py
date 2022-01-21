from envs import env
from jwt import DecodeError, ExpiredSignatureError, MissingRequiredClaimError, ImmatureSignatureError, \
    InvalidAudienceError, InvalidAlgorithmError, InvalidIssuerError, InvalidIssuedAtError, InvalidKeyError, \
    InvalidTokenError, InvalidSignatureError

from pfunk.exceptions import TokenValidationFailed


class AuthMiddleware(object):
    """ Authentication middleware for easier process of auth flow. """

    def process_request(self, request):
        """Acquires cookie from the request, gets the jwt and validate it.

        Args:
            request (`web.request.Request`, required):
                request of the view
        
        Returns:
            request (`web.request.Request`, required):
                processed request with added `claims` key as
                the decrypted key

        Raises:
            TokenValidationFailed: Validation of token was failed
        """

        cookies = request.cookies
        cookie_name = env('CORKY_JWT_COOKIE', 'jwt')
        try:
            jwt_ = request.cookies.get(env('JWT_COOKIE', 'jwt'), None)
            claims = Key.decrypt_jwt(jwt_)
        except (DecodeError, ExpiredSignatureError, MissingRequiredClaimError,
                ImmatureSignatureError, InvalidAudienceError, InvalidAlgorithmError,
                InvalidIssuerError, InvalidIssuedAtError, InvalidKeyError,
                InvalidTokenError, KeyError, InvalidSignatureError):
            raise TokenValidationFailed('JWT Validation Failed')
        request.claims = claims
        return request

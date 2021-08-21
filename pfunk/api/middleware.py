from envs import env
from jwt import DecodeError, ExpiredSignatureError, MissingRequiredClaimError, ImmatureSignatureError, \
    InvalidAudienceError, InvalidAlgorithmError, InvalidIssuerError, InvalidIssuedAtError, InvalidKeyError, \
    InvalidTokenError, InvalidSignatureError

from pfunk.exceptions import TokenValidationFailed


class AuthMiddleware(object):

    def process_request(self, request):

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



class LoginFailed(Exception):
    """Exception raised when an attempt to login fails."""
    pass


class DocNotFound(Exception):
    """Exception raised when a document is not found."""
    pass


class TokenValidationFailed(Exception):
    """Exception raised when a JWT validation fails"""
    pass


class Unauthorized(Exception):
    """Exception raised when the request is not authorized"""
    pass


class GraphQLError(Exception):
    """Graphql SyntaxError"""
    pass
from pfunk.api.http import HttpNotFoundResponse


class LoginFailed(Exception):
    """Exception raised when an attempt to login fails."""
    pass


class DocNotFound(Exception):
    """Exception raised when a document is not found."""
    pass


class TokenValidationFailed(Exception):
    """Exception raised when a JWT validation fails"""
    pass

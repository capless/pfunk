class LoginFailed(Exception):
    """Exception raised when an attempt to login fails."""
    pass


class DocNotFound(Exception):
    """Exception raised when a document is not found."""
    pass

"""Custom cleanair exceptions"""


class UrbanairException(Exception):
    """Urbanair specific exception"""


class UrbanairAzureException(UrbanairException):
    """Azure specific exception for the urbanair project"""


class MissingFeatureError(UrbanairException):
    """Raised when a feature is missing in the database"""


class MissingSourceError(UrbanairException):
    """Raised when a source is missing in the database"""


class AuthenticationException(UrbanairException):
    """Raised when a user cannot be authenticated"""


class DatabaseAuthenticationException(AuthenticationException):
    """Raised when a user cannot be authenticated by the database"""


class DatabaseUserAuthenticationException(DatabaseAuthenticationException):
    """Raised when Azure could not find the active user"""

    DEFAULT_MESSAGE = "Could not get active user from Azure. Have you run 'az login'?"

    def __init__(self, *args):
        if args:
            super().__init__(*args)
        else:
            super().__init__(self.DEFAULT_MESSAGE)


class DatabaseAccessTokenException(DatabaseAuthenticationException):
    """Raised when Azure could not find the active user"""

    DEFAULT_MESSAGE = "Failed to get an access token from Azure. Do you have DB access?"

    def __init__(self, *args):
        if args:
            super().__init__(*args)
        else:
            super().__init__(self.DEFAULT_MESSAGE)

"""CleanAir Exceptions"""

from .exceptions import (
    AuthenticationException,
    DatabaseAuthenticationException,
    DatabaseAccessTokenException,
    DatabaseUserAuthenticationException,
    MissingFeatureError,
    MissingSourceError,
    UrbanairException,
)

__all__ = [
    "AuthenticationException",
    "DatabaseAuthenticationException",
    "DatabaseAccessTokenException",
    "DatabaseUserAuthenticationException",
    "MissingFeatureError",
    "MissingSourceError",
    "UrbanairException",
]

"""Custom cleanair exceptions"""


class MissingFeatureError(Exception):
    """Raised when a feature is missing in the database"""


class MissingSourceError(Exception):
    """Raised when a source is missing in the database"""
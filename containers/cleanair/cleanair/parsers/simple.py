"""
Simple per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser
from ..mixins import (
    SecretFileParserMixin,
    DurationParserMixin,
    InsertMethodMixin,
    VerbosityMixin,
    SourcesMixin,
    WebMixin,
)


class SecretFileParser(SecretFileParserMixin, ArgumentParser):
    """
    Parser for any entrypoint which needs a secrets file
    """


class VerbosityParser(VerbosityMixin, ArgumentParser):
    """
    Parser for any entrypoint which allows verbosity to be set
    """


class SourcesParser(SecretFileParserMixin, ArgumentParser):
    """
    Parser for any entrypoint which allows verbosity to be set
    """


class DurationParser(DurationParserMixin, ArgumentParser):

    """
    Parser for any entrypoint which needs a duration
    """
    
class WebParser(WebMixin, ArgumentParser):
    """
    Parser for any entrypoint which allows verbosity to be set
    """


class InsertMethodParser(InsertMethodMixin, ArgumentParser):
    """
    Parser for any entrypoint that requires an insert method
    """


class StaticFeatureArgumentParser(
    SecretFileParserMixin, VerbosityMixin, ArgumentParser,
):
    """Static feature Parser"""


class SourceParser(SourcesMixin, ArgumentParser):
    """Sources Parser"""


class AQEReadingArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for AQE readings"""


class LAQNReadingArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for LAQN readings"""


class ScootReadingFeatureArgumentParser(
    DurationParserMixin,
    SecretFileParserMixin,
    SourcesMixin,
    VerbosityMixin,
    ArgumentParser,
):
    """Argument parsing for converting SCOOT readings into model features"""


class ScootRoadmapArgumentParser(SecretFileParserMixin, VerbosityMixin, ArgumentParser):
    """Argument parsing for SCOOT road to detector mapping"""


class StreetCanyonFeatureArgumentParser(
    SourcesMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for OS highway features"""


class StaticDatasetArgumentParser(
    SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for static dataset uploads"""


class UKMapFeatureArgumentParser(
    SourcesMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for OS highway features"""

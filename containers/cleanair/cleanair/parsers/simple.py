"""
Simple per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser
from ..mixins import (
    SecretFileParserMixin,
    SourcesMixin,
    DurationParserMixin,
    VerbosityMixin,
)


class AQEReadingArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for AQE readings"""


class LAQNReadingArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for LAQN readings"""


class OsHighwayFeatureArgumentParser(
     SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """OsHighway Parser"""

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

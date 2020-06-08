"""Parsers for feature processing entrypoints"""
from argparse import ArgumentParser
from cleanair.parsers import (
    SatelliteArgumentParser,
    SecretFileParser,
    VerbosityParser,
    SourceParser,
    DurationParser,
    WebParser,
    InsertMethodParser,
    FeatureNameParser,
    FeatureSourceParser,
)


def create_static_feature_parser(check, fill, all_source_names, all_features):
    """
    Create a parser for the static feature processor

    Arguments:
        check (func): A function called check which checks what is in a database and what needs processing
        fill (func): A functin called fill which processes data and inserts it into a database
    """

    # Parser parent mixins
    secret_parser = SecretFileParser(add_help=False)
    verbosity_parser = VerbosityParser(add_help=False)
    web_parser = WebParser(add_help=False)
    insert_method_parser = InsertMethodParser(add_help=False)
    source_parser = SourceParser(sources=["laqn", "aqe"], add_help=False)
    feature_name_parser = FeatureNameParser(all_features, add_help=False)
    feature_source_parser = FeatureSourceParser(
        feature_sources=all_source_names, add_help=False
    )

    # Define parsers with arguments that apply to all commands
    main_parser = ArgumentParser(
        description="Extract static features and check what is in database"
    )

    # subparsers
    subparsers = main_parser.add_subparsers(required=True, dest="command")
    parser_check = subparsers.add_parser(
        "check",
        help="Check what satellite readings are available in the cleanair database",
        parents=[
            feature_source_parser,
            source_parser,
            feature_name_parser,
            secret_parser,
            verbosity_parser,
            web_parser,
            insert_method_parser,
        ],
    )
    parser_insert = subparsers.add_parser(
        "fill",
        help="Read satellite data from the Copernicus API and insert into the database",
        parents=[
            feature_source_parser,
            source_parser,
            feature_name_parser,
            secret_parser,
            verbosity_parser,
            insert_method_parser,
        ],
    )

    # Link to programs
    parser_check.set_defaults(func=check)
    parser_insert.set_defaults(func=fill)

    return main_parser


def create_satellite_input_parser(check, fill):
    """
    Create a parser for the static feature processor

    Arguments:
        check (func): A function called check which checks what is in a database and what needs processing
        fill (func): A functin called fill which processes data and inserts it into a database
    """

    # Parser parent mixins
    secret_parser = SecretFileParser(add_help=False)
    verbosity_parser = VerbosityParser(add_help=False)
    duration_parser = DurationParser(ndays=5, end="tomorrow", add_help=False)
    web_parser = WebParser(add_help=False)
    insert_method_parser = InsertMethodParser(add_help=False)
    copernicus_key_parser = SatelliteArgumentParser(add_help=False)

    # Define parsers with arguments that apply to all commands
    main_parser = ArgumentParser()

    # Subparsers
    subparsers = main_parser.add_subparsers(required=True, dest="command")
    parser_check = subparsers.add_parser(
        "check",
        help="Check what satellite readings are available in the cleanair database",
        parents=[secret_parser, verbosity_parser, duration_parser, web_parser,],
    )
    parser_insert = subparsers.add_parser(
        "fill",
        help="Read satellite data from the Copernicus API and insert into the database",
        parents=[
            secret_parser,
            verbosity_parser,
            copernicus_key_parser,
            duration_parser,
            insert_method_parser,
        ],
    )

    # Link to programs
    parser_check.set_defaults(func=check)
    parser_insert.set_defaults(func=fill)

    return main_parser

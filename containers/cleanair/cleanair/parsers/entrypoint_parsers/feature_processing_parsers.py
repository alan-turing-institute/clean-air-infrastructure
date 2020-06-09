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
)


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
    source_parser = SourceParser(sources=["laqn", "aqe"], add_help=False)
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
        parents=[
            secret_parser,
            verbosity_parser,
            source_parser,
            duration_parser,
            web_parser,
        ],
        add_help=False,
    )
    parser_insert = subparsers.add_parser(
        "fill",
        help="Read satellite data from the Copernicus API and insert into the database",
        parents=[
            secret_parser,
            verbosity_parser,
            copernicus_key_parser,
            source_parser,
            duration_parser,
            insert_method_parser,
        ],
        add_help=False,
    )

    # Link to programs
    parser_check.set_defaults(func=check)
    parser_insert.set_defaults(func=fill)

    return main_parser

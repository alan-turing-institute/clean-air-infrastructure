"""
Run feature processing using OSHighway data
"""
import webbrowser
import tempfile
import time
from argparse import ArgumentParser
from cleanair.loggers import initialise_logging
from cleanair.features import FeatureExtractor, FEATURE_CONFIG
from cleanair.parsers.entrypoint_parsers import create_static_feature_parser

ALL_FEATURES = [
    val
    for sublist in [
        list(j.keys()) for j in [ftype["features"] for ftype in FEATURE_CONFIG.values()]
    ]
    for val in sublist
]


def check(args):
    """Check what data is available in the database"""

    # Set up feature extractor
    static_feature_extractor = FeatureExtractor(
        feature_source=args.feature_source,
        table=FEATURE_CONFIG[args.feature_source]["table"],
        features=FEATURE_CONFIG[args.feature_source]["features"],
        secretfile=args.secretfile,
        sources=args.sources,
    )

    if not args.feature_name:
        args.feature_name = list(FEATURE_CONFIG[args.feature_source]["features"].keys())

    if args.method == "all":
        exclude_missing = False
    else:
        exclude_missing = True

    # Set up features to check
    if args.web:
        # show in browser
        available_data = static_feature_extractor.get_static_feature_availability(
            args.feature_name, args.sources, exclude_missing, output_type="html"
        )

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write(
                "<h1>Feature availability. Feature={}</h1>".format(args.feature_name)
            )
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = static_feature_extractor.get_static_feature_availability(
            args.feature_name, args.sources, exclude_missing, output_type="tabulate",
        )

        print(available_data)


def fill(args):
    """Fill the database"""

    # Set up feature extractor
    static_feature_extractor = FeatureExtractor(
        feature_source=args.feature_source,
        table=FEATURE_CONFIG[args.feature_source]["table"],
        features=FEATURE_CONFIG[args.feature_source]["features"],
        secretfile=args.secretfile,
        sources=args.sources,
    )

    static_feature_extractor.update_remote_tables()


def create_parser():
    """Create parser"""

    print(FEATURE_CONFIG.keys())
    quit()

    secret_parser = SecretFileParser(add_help=False)
    verbosity_parser = VerbosityParser(add_help=False)
    source_parser = SourceParser(sources=["laqn", "aqe"], add_help=False)
    feature_source_parser = FeatureSourceParser(
        feature_sources=FEATURE_CONFIG.keys(), add_help=False
    )
    feature_name_parser = FeatureNameParser(ALL_FEATURES, add_help=False)

    main_parser = ArgumentParser(
        description="Extract static features and check what is in database",
    )

    # Create subparser
    subparsers = main_parser.add_subparsers(required=True, dest="command")
    parser_check = subparsers.add_parser(
        "check",
        help="Check what static features are available in the cleanair database",
        parents=[feature_source_parser, feature_name_parser, source_parser],
    )
    parser_check.add_argument(
        "--exclude-has-data", default=False, action="store_true",
    )
    parser_check.add_argument(
        "-w",
        "--web",
        default=False,
        action="store_true",
        help="Open a browser to show available data. Else print to console",
    )

    parser_insert = subparsers.add_parser(
        "fill",
        help="Process static features",
        parents=[feature_source_parser, feature_name_parser, source_parser],
    )

    parser_insert.add_argument(
        "-m", "--method", default="missing", type=str, choices=["missing", "all"]
    )

    # #     # # Link to programs
    parser_check.set_defaults(func=check)
    parser_insert.set_defaults(func=fill)

    return main_parser


def main():
    """
    Extract static OSHighway features
    """

    # Parse and interpret command line arguments
    args = create_static_feature_parser(
        check, fill, FEATURE_CONFIG.keys(), ALL_FEATURES
    ).parse_args()

    # Execute program
    args.func(args)


if __name__ == "__main__":
    main()

"""
Run feature processing using OSHighway data
"""
import webbrowser
import tempfile
import time
from cleanair.loggers import initialise_logging
from cleanair.features import OSHighwayFeatures
from cleanair.parsers import OsHighwayFeatureArgumentParser


def check(args):
    """Check what data is available in the database"""

    
    static_feature_extractor = OSHighwayFeatures(
        secretfile=args.secretfile, sources=None
    )

    if args.web:
        # show in browser
        available_data = static_feature_extractor.get_static_feature_availability(args.feature_name, args.source, args.exclude_has_data, output_type='html')

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write("<h1>Feature availability. Feature={}</h1>".format(args.feature_name))
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data =  static_feature_extractor.get_static_feature_availability(args.feature_name, args.source, args.exclude_has_data, output_type='tabulate')

        print(available_data)

    # Extract static features into the appropriate tables on the database
    static_feature_extractor.get_static_feature_availability(args.feature_name, args.source, args.exclude_has_data)


def fill(args):
    """Fill the database"""

    static_feature_extractor = OSHighwayFeatures(
        secretfile=args.secretfile, sources=None
    )

    static_feature_extractor.update_remote_tables()

def create_parser():
    """Create parser"""

    # Parse and interpret command line arguments
    parsers = OsHighwayFeatureArgumentParser(
        description="Extract static OSHighway features and check what is in database"
    )

    subparsers = parsers.add_subparsers(required=True, dest="command")

    parser_check = subparsers.add_parser(
        "check",
        help="Check what static features are available in the cleanair database",
    )

    # parser_insert = subparsers.add_parser(
    #     "fill",
    #     help="Process static features",
    # )

    # parser_insert.add_argument(
    #     "-m", "--method", default="missing", type=str, choices=["missing", "all"]
    # )

    parser_check.add_argument(
        "-f",
        "--feature-name",
        required=True,
        type=str,
    )
    parser_check.add_argument(
        "--source",
        type=str,
    )
    parser_check.add_argument(
        "--exclude-has-data",
        default=False,
        action="store_true",
    )
    parser_check.add_argument(
        "-w",
        "--web",
        default=False,
        action="store_true",
        help="Open a browser to show available data. Else print to console",
    )

    # # Link to programs
    parser_check.set_defaults(func=check)
    # parser_insert.set_defaults(func=fill)

    return parsers

def main():
    """
    Extract static OSHighway features
    """

    # Parse and interpret command line arguments
    args = create_parser().parse_args()

    # Execute program
    args.func(args)


    # # Parse and interpret command line arguments
    # args = OsHighwayFeatureArgumentParser(
    #     description="Extract static OSHighway features",
    #     sources=["aqe", "laqn", "satellite", "hexgrid"],
    # ).parse_args()

    # # Set logging verbosity
    # default_logger = initialise_logging(args.verbose)

    # # Update OSHighway features on the database, logging any unhandled exceptions
    # try:
    #     static_feature_extractor = OSHighwayFeatures(
    #         secretfile=args.secretfile, sources=args.sources
    #     )
    #     # Extract static features into the appropriate tables on the database
    #     static_feature_extractor.update_remote_tables()

    # except Exception as error:
    #     default_logger.error("An uncaught exception occurred: %s", str(error))
    #     raise


if __name__ == "__main__":
    main()

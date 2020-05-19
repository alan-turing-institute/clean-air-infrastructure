"""
Add satellite readings to database
"""
from cleanair.inputs import SatelliteWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import SatelliteArgumentParser


def check():
    pass


def fill():
    pass


def create_parser():
    "Create parser"
    parsers = SatelliteArgumentParser()
    # Subparsers
    subparsers = parsers.add_subparsers(required=True, dest="command")
    parser_generate = subparsers.add_parser(
        "check", help="Check what satellite readings are available in the database",
    )
    parser_insert = subparsers.add_parser(
        "fill",
        help="Read satellite data from the Copernicus API and insert into the database",
    )

    # Link to programs
    parser_generate.set_defaults(func=check)
    parser_insert.set_defaults(func=fill)

    return parsers


def main():
    """
    Update satellite table
    """
    # Parse and interpret command line arguments
    args = create_parser().parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update the satellite forecast table on the database, logging any unhandled exceptions
    try:
        satellite_writer = SatelliteWriter(
            copernicus_key=args.copernicus_key,
            end=args.end,
            nhours=args.nhours,
            secretfile=args.secretfile,
            secret_dict=args.secret_dict,
        )
        satellite_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

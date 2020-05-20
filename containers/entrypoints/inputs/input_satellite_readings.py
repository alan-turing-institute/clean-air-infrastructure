"""
Add satellite readings to database
"""
from cleanair.inputs import SatelliteWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import SatelliteArgumentParser


def check():
    pass


def fill(args):

    # Update the satellite forecast table on the database, logging any unhandled exceptions

    print(args)
    satellite_writer = SatelliteWriter(
        copernicus_key=args.copernicus_key,
        end=args.end,
        nhours=args.nhours,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
        method= args.method
    )

    satellite_writer.update_remote_tables()

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

    parser_insert.add_argument("-m", "--method", default = 'missing', type=str, choices=["missing", "all"])

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

    # Execute program
    args.func(args)
    

if __name__ == "__main__":
    main()

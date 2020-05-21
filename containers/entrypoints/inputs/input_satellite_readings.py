"""
Add satellite readings to database
"""
import webbrowser
import tempfile
import time
from cleanair.inputs import SatelliteWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import SatelliteArgumentParser


def check(args):
    # Update the satellite forecast table on the database, logging any unhandled exceptions

    satellite_writer = SatelliteWriter(
        copernicus_key=args.copernicus_key,
        end=args.end,
        nhours=args.nhours,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
    )

    if args.web:
        "Show in a browser"
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date,
            reference_end_date=satellite_writer.end_date,
            output_type="html",
        )

        with tempfile.NamedTemporaryFile(suffix='.html', mode='w') as tmp:
            tmp.write("<h1>Satellite data availability</h1>")
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open('file://' + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date,
            reference_end_date=satellite_writer.end_date,
            output_type="tabulate",
        )

        print(available_data)

def fill(args):

    # Update the satellite forecast table on the database, logging any unhandled exceptions
    satellite_writer = SatelliteWriter(
        copernicus_key=args.copernicus_key,
        end=args.end,
        nhours=args.nhours,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
        method=args.method,
    )

    satellite_writer.update_remote_tables()


def create_parser():
    "Create parser"
    parsers = SatelliteArgumentParser()
    # Subparsers
    subparsers = parsers.add_subparsers(required=True, dest="command")
    parser_check = subparsers.add_parser(
        "check", help="Check what satellite readings are available in the cleanair database",
    )

    parser_insert = subparsers.add_parser(
        "fill",
        help="Read satellite data from the Copernicus API and insert into the database",
    )

    parser_insert.add_argument(
        "-m", "--method", default="missing", type=str, choices=["missing", "all"]
    )

    parser_check.add_argument('-w', '--web', default=False, action='store_true', help="Open a browser to show available data. Else print to console")

    # Link to programs
    parser_check.set_defaults(func=check)
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

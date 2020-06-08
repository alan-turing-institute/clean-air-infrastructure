"""
Add satellite readings to database
"""
import webbrowser
import tempfile
import time
from argparse import ArgumentParser
from cleanair.inputs import SatelliteWriter
from cleanair.parsers.entrypoint_parsers import create_satellite_input_parser
from cleanair.parsers import (
    SecretFileParser,
    VerbosityParser,
    SourceParser,
    DurationParser,
    WebParser,
    InsertMethodParser,
)


def check(args):
    """Check what data is available in the database"""
    # Update the satellite forecast table on the database, logging any unhandled exceptions

    satellite_writer = SatelliteWriter(
        copernicus_key=None,
        end=args.upto,
        nhours=args.nhours,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
    )

    if args.web:
        # show in browser
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date.isoformat(),
            reference_end_date=satellite_writer.end_date.isoformat(),
            output_type="html",
        )

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write("<h1>Satellite data availability</h1>")
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date.isoformat(),
            reference_end_date=satellite_writer.end_date.isoformat(),
            output_type="tabulate",
        )

        print(available_data)


def fill(args):
    """Call the API and fill the database"""
    # Update the satellite forecast table on the database, logging any unhandled exceptions
    satellite_writer = SatelliteWriter(
        copernicus_key=args.copernicus_key,
        end=args.upto,
        nhours=args.nhours,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
        method=args.method,
    )

    satellite_writer.update_remote_tables()



def main():
    """
    Update satellite table
    """
    # Parse and interpret command line arguments
    args = create_satellite_input_parser(check, fill).parse_args()

    # Execute program
    args.func(args)


if __name__ == "__main__":
    main()

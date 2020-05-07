"""
Add satellite readings to database
"""
from cleanair.inputs import SatelliteWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import SatelliteArgumentParser


def main():
    """
    Update satellite table
    """
    # Parse and interpret command line arguments
    args = SatelliteArgumentParser(description="Get satellite data").parse_args()

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

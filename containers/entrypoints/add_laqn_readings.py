"""
Add LAQN readings to database
"""
from cleanair.inputs import LAQNWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import LAQNReadingArgumentParser


def main():
    """
    Update LAQN table
    """
    # Parse and interpret command line arguments
    args = LAQNReadingArgumentParser(description="Get LAQN sensor data").parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update the LAQN tables on the database, logging any unhandled exceptions
    try:
        laqn_writer = LAQNWriter(end=args.end, nhours=args.nhours, secretfile=args.secretfile)
        laqn_writer.update_remote_tables()
    except Exception as error:
        default_logger.info("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

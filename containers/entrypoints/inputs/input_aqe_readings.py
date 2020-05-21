"""
Add AQE readings to database
"""
from cleanair.inputs import AQEWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import AQEReadingArgumentParser


def main():
    """
    Update AQE table
    """
    # Parse and interpret command line arguments
    args = AQEReadingArgumentParser(description="Get AQE sensor data").parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update the AQE tables on the database, logging any unhandled exceptions
    try:
        aqe_writer = AQEWriter(
            end=args.end,
            nhours=args.nhours,
            secretfile=args.secretfile,
            secret_dict=args.secret_dict,
        )
        aqe_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

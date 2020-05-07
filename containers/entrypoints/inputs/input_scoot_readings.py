"""
Add SCOOT readings to database
"""
from cleanair.inputs import ScootWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import ScootReadingArgumentParser


def main():
    """
    Update SCOOT table
    """
    # Parse and interpret command line arguments
    args = ScootReadingArgumentParser(description="Get SCOOT traffic data").parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update the SCOOT reading table on the database, logging any unhandled exceptions
    try:
        scoot_writer = ScootWriter(
            end=args.end,
            aws_key_id=args.aws_key_id,
            aws_key=args.aws_key,
            nhours=args.nhours,
            secretfile=args.secretfile,
            secret_dict=args.secret_dict,
        )
        scoot_writer.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

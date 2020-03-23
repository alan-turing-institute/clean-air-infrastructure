"""
Upload static datasets
"""
from cleanair.inputs import StaticWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import StaticDatasetArgumentParser


def main():
    """
    Upload static datasets
    """
    # Parse and interpret command line arguments
    args = StaticDatasetArgumentParser(
        description="Upload a static dataset"
    ).parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update static data to the database, logging any unhandled exceptions
    try:
        static_writer = StaticWriter(secretfile=args.secretfile)
        static_writer.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

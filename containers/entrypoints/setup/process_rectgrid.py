"""
Upload static datasets
"""
from cleanair.inputs import RectGridWriter
from cleanair.loggers import initialise_logging
from cleanair.parsers import StaticDatasetArgumentParser


def main():
    """
    Upload rectangular grid data
    """
    # Parse and interpret command line arguments
    args = StaticDatasetArgumentParser(
        description="Upload rectangular grid data"
    ).parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update rectangular grid data to the database, logging any unhandled exceptions
    try:
        rectgrid_writer = RectGridWriter(secretfile=args.secretfile)
        rectgrid_writer.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()

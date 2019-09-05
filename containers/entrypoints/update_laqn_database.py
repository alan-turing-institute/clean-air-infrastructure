"""
Update laqn database
"""
import argparse
import datasources


def main():
    """
    Update laqn database
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get LAQN sensor data")
    parser.add_argument("-e", "--end", type=str, default="yesterday",
                        help="The last date (YYYY-MM-DD) to get data for.")
    parser.add_argument("-n", "--ndays", type=int, default=2, help="The number of days to request data for.")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Perform update and notify any exceptions
    try:
        laqndb = datasources.LAQNDatabase(**vars(args))

        # Update the LAQN tables on the database
        laqndb.update_remote_tables()
    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()

"""
Update static dataset
"""
import argparse
import cleanair


def main():
    """
    Update static dataset
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Insert static datasets")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Perform update and notify any exceptions
    try:
        staticdb = cleanair.StaticDatabase(**vars(args))

        # Upload static files
        staticdb.upload_static_files()

        # Configure database tables
        staticdb.configure_tables()
    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()

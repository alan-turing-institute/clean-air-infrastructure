import argparse
import datasources


def main():
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Insert static datasets")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    staticdb = datasources.StaticDatabase(**vars(args))

    # Upload static files
    staticdb.upload_static_files()

    # Configure database tables
    staticdb.configure_tables()


if __name__ == "__main__":
    main()

import argparse
import datasources

if __name__ == "__main__":
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get LAQN sensor data")
    parser.add_argument("-s", "--secretfile", default=".static_secret.json", help="File containing connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    staticdb = datasources.StaticDatabase(**vars(args))

    # Upload static files
    staticdb.upload_static_files()

    # Configure database
    staticdb.configure_database()

"""
Upload static datasets
"""
import argparse
from cleanair.inputs import RectGridWriter


def main():
    """
    Upload square grid data
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Insert static datasets")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Perform update and notify any exceptions
    try:
        rectgrid_writer = RectGridWriter(**vars(args))

        # Attempt to upload static files and configure the tables if successful
        # if rectgrid_writer.upload_static_files():
        rectgrid_writer.upload_grid_data()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()

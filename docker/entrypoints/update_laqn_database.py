import argparse
import datasources

if __name__ == "__main__":
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get LAQN sensor data")
    parser.add_argument("-e", "--end", type=str, default="today", help="The last date (YYYY-MM-DD) to get data for.")
    parser.add_argument("-n", "--ndays", type=int, default=2, help="The number of days to request data for.")
    parser.add_argument("-s", "--secretfile", default=".db_inputs_secret.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    laqndb = datasources.LAQNDatabase(**vars(args))

    # Update the laqn_sites database table
    laqndb.update_site_list_table()

    # Update data in laqn reading table
    laqndb.update_reading_table()

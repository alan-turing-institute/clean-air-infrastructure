import argparse
import json
import logging
import os
import requests
import termcolor
from datetime import timedelta, datetime

ONE_DAY = timedelta(days=1)


def days(d):
    """Time delta in days"""
    return timedelta(days=d)


def green(text):
    return termcolor.colored(text, "green")


def red(text):
    return termcolor.colored(text, "red")


def connected_to_internet(url="http://www.google.com/", timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False


def dict_clean(dictionary):
    """Coerce missing keys to 'None'"""
    for key in dictionary.keys():
        if not dictionary[key]:
            dictionary[key] = None
    return dictionary


def drop_duplicates(data):
    """If the data from the API contains duplicates then drop them"""
    deduped_list = [dict(t) for t in {tuple(d.items()) for d in data}]
    n_dropped = len(deduped_list) - len(data)

    if n_dropped > 0:
        logging.warning("Dropped %s data points", n_dropped)
        return deduped_list
    return data


def str_to_datetime(date_str):
    """Get a datetime from a known-format string"""
    return datetime.strptime(date_str, "%Y-%m-%d")


def emptystr_2_none(x):
    """Convert empty strings to None"""
    if isinstance(x, str) and (x == ''):
        return None
    else:
        return x


def map_dict(d1, f):
    """Map a function to every item in a dictionary"""
    d2 = {k: f(v) for k, v in d1.items()}
    return d2


def datetime_floor(dtime):
    """Set the time to midnight for a given datetime"""
    return datetime.combine(dtime, datetime.min.time())


def get_data_range(site, start_date, end_date):
    """
    Get the dates that data is available for a site between start_date and end_date
    If no data is available between these dates returns None
    """
    if not start_date:
        get_data_from = datetime_floor(site.DateOpened)
    else:
        get_data_from = max([datetime_floor(site.DateOpened), datetime_floor(str_to_datetime(start_date))])

    if not end_date:
        if not site.DateClosed:
            get_data_to = datetime.today()
        else:
            get_data_to = min([datetime_floor(datetime.today()), datetime_floor(site.DateClosed)])

    else:
        if not site.DateClosed:
            get_data_to = datetime_floor(str_to_datetime(end_date))
        else:
            # Site is closed to get data until that point
            get_data_to = min([datetime_floor(str_to_datetime(end_date)), datetime_floor(site.DateClosed)])

    delta = get_data_to - get_data_from  # Number of days available for a site

    if delta.days < 0:
        return None
    return (get_data_from, get_data_to)


def load_db_info(secret_file):
    """
    Loads database secrets from a json file.
    Check file system is accessable from docker and return database login info
    """

    mount_dir = 'secrets'
    local_dir = './terraform/.secrets/'

    # Check if the following directories exist
    check_secrets_mount = os.path.isdir(mount_dir)
    check_local_dir = os.path.isdir(local_dir)

    secret_fname = None
    if check_secrets_mount:
        logging.info("%s is mounted", mount_dir)
        secret_fname = os.path.join(mount_dir, secret_file)

    elif check_local_dir:
        logging.info("%s exists locally", check_local_dir)
        secret_fname = os.path.join(local_dir, secret_file)

    else:
        raise FileNotFoundError("Database secrets could not be found. "
                                "Check that either {} is mounted or {} exists locally".format(mount_dir, local_dir))

    try:
        with open(secret_fname) as f:
            data = json.load(f)
        logging.info("Database connection information loaded")

    except FileNotFoundError:
        logging.error("Database secrets could not be found. Ensure secret_file exists")
        raise FileNotFoundError

    return data


def create_connection_string(host, port, dbname, user, password):
    """
    Create a postgres connection string
    """
    connection_string = "postgresql://{}:{}@{}:{}/{}".format(
        user, password, host, port, dbname)
    return connection_string


def process_args():
    # Read command line arguments
    parser = argparse.ArgumentParser(description='Get sensor data')

    parser.add_argument("-e", "--end", type=str, default="today",
                        help="The last date to get data for in international standard date notation (YYYY-MM-DD)")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-n", "--ndays", type=int, default=2,
                       help="The number of days to request data for. ndays=1 will get today (from midnight)")
    group.add_argument("-s", "--start", type=str,
                       help="The first date to get data for in international standard date notation (YYYY-MM-DD). "
                            "If --ndays is provided this argument is ignored. Will get data from midnight")
    parser.add_argument('-f', "--force", action="store_true",
                        help="Attempt to write to database even if data for that date is already in database. "
                             "This is done for todays date regardless of whether -f is given")
    parser.add_argument("-d", "--debug", action="store_true", help="Set the logger level to debug")
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s",
                        datefmt=r"%Y-%m-%d %H:%M:%S", level=log_level)

    # Set the end date
    if args.end == 'today':
        args.end = datetime.today().date()
    else:
        args.end = datetime.strptime(args.end, "%Y-%m-%d").date()

    # Set the start date
    if args.ndays is not None:
        if args.ndays < 1:
            raise argparse.ArgumentTypeError(
                "Argument --ndays must be greater than 0")
        args.start = args.end - days(args.ndays - 1)
    else:
        args.start = datetime.strptime(args.start, "%Y-%m-%d").date()

    logging.info("AQE data. Request Start date = %s to: End date = %s. "
                 "Data is collected from %s on the start date until %s on the end date. "
                 "Force is set %s - when True will try to write each entry to the database",
                 green(args.start), green(args.end), red("00:00:00"), red("23:59:59"), green(args.force))

    return args.start, args.end, args.force

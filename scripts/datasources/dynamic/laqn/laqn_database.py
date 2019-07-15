"""
Get data from the LAQN network via the API maintained by Kings Colleage London (https://www.londonair.org.uk/Londonair/API/)
"""

import argparse
import requests
import os
import json
import logging
import termcolor

from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, create_engine, exists, and_
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import timedelta, datetime


def days(d):
    "Time delta in days"
    return timedelta(days=d)


logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s",
                    datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)

ONE_DAY = timedelta(days=1)


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


def get_site_info():
    """
    Get info on all laqn sites
    """
    r = requests.get(
        "http://api.erg.kcl.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json", timeout=5.)

    if r.status_code == 200:
        site_list = r.json()["Sites"]["Site"]
        return site_list
    return None


def get_site_reading(sitecode, start_date, end_date):
    """
    Request data for a given {sitecode} between {start_date} and {end_date}. Dates given in %yyyy-mm-dd%
    """
    r = requests.get(
        "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(sitecode,
                                                                                                        start_date, end_date))

    if r.status_code == 200:
        data = r.json()["AirQualityData"]["Data"]
        return drop_duplicates(data)
    return None


def drop_duplicates(data):
    """
    If the data from the KCL api contains duplicates then drop them
    """
    deduped_list = [dict(t) for t in {tuple(d.items()) for d in data}]
    n_dropped = len(deduped_list) - len(data)

    if n_dropped > 0:
        logging.warning("Dropped %s data points", n_dropped)
        return deduped_list
    return data


def dict_clean(dictionary):
    """
    Coerce missing keys to 'None'
    """
    for key in dictionary.keys():
        if not dictionary[key]:
            dictionary[key] = None
    return dictionary


def str_to_datetime(date_str):
    """
    Get a datetime from a known-format string
    """
    return datetime.strptime(date_str, "%Y-%m-%d")

def emptystr_2_none(x):
    """
    Convert empty strings to None
    """

    if isinstance(x, str) and (x == ''):
        return None
    else:
        return x

def map_dict(d1, f):
    """
    Map a function to every item in a dictionary
    """

    d2 = {k: f(v) for k, v in d1.items()}
    return d2

# Database tables
Base = declarative_base()

class laqn_sites(Base):
    """
    Table of LAQN sites
    """
    __tablename__ = "laqn_sites"
    SiteCode = Column(String(4), primary_key=True, nullable=False)
    la_id = Column(Integer, nullable=False)
    SiteType = Column(String(20), nullable=False)
    os_grid_x = Column(DOUBLE_PRECISION)
    os_grid_y = Column(DOUBLE_PRECISION)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)
    geom = Column(Geometry(geometry_type="POINT", srid=4326,
                           dimension=2, spatial_index=True))


class laqn_reading(Base):
    """
    Table of LAQN readings
    """
    __tablename__ = "laqn_readings"
    SiteCode = Column(String(4), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def create_connection_string(host, port, dbname, user, password):
    """
    Create a postgres connection string
    """
    connection_string = "postgresql://{}:{}@{}:{}/{}".format(
        user, password, host, port, dbname)
    return connection_string


def site_to_laqn_site_entry(site):
    """
    Create an laqn_sites entry
    """
    
    site = map_dict(site, emptystr_2_none)

    # Hack to make geom = NULL if longitude and latitude dont exist
    if (site['@Longitude'] is None) or (site['@Latitude'] is None):
        out = laqn_sites(SiteCode=site['@SiteCode'],
                         la_id=site['@LocalAuthorityCode'],
                         SiteType=site['@SiteType'],
                         Latitude=site['@Latitude'],
                         Longitude=site['@Longitude'],
                         DateOpened=site['@DateOpened'],
                         DateClosed=site['@DateClosed']
                         )

    else:
        geom_string = 'SRID=4326;POINT({} {})'.format(
            site['@Longitude'], site['@Latitude'])
        out = laqn_sites(SiteCode=site['@SiteCode'],
                         la_id=site['@LocalAuthorityCode'],
                         SiteType=site['@SiteType'],
                         Latitude=site['@Latitude'],
                         Longitude=site['@Longitude'],
                         DateOpened=site['@DateOpened'],
                         DateClosed=site['@DateClosed'],
                         geom=geom_string
                         )

    return out


def laqn_reading_entry(reading):
    """
    Create an laqn_read entry
    """
    reading = dict_clean(reading)
    return laqn_reading(SiteCode=reading["@SiteCode"],
                        SpeciesCode=reading["@SpeciesCode"],
                        MeasurementDateGMT=reading["@MeasurementDateGMT"],
                        Value=reading["@Value"])


def create_sitelist(site_info):
    """
    Return a list of laqn_site objects
    """
    all_sites = []
    for site in site_info:
        all_sites.append(site_to_laqn_site_entry(site))
    return all_sites


def update_site_list_table(session):
    """
    Update the site info
    """

    # Update site info
    logging.info("Requesting site info from %s", green("KCL API"))
    site_info = get_site_info()

    # Query site_info entires
    site_info_query = session.query(laqn_sites)

    # Check if database table is empty
    if not site_info_query.all():
        logging.info("Database is empty. Inserting all entries")
        site_db_entries = create_sitelist(site_info)
        session.add_all(site_db_entries)
        session.commit()

    # If not empty check it has latest information
    else:
        # Check if site exists and database is up to date
        logging.info("Crosscheck entries in database table %s",
                     green(laqn_sites.__tablename__))

        for site in site_info:

            # Check if site exists
            site_exists = session.query(exists().where(
                laqn_sites.SiteCode == site["@SiteCode"])).scalar()

            if not site_exists:
                logging.info("Site %s not in %s. Creating entry", green(
                    site["@SiteCode"]), green(laqn_sites.__tablename__))
                site_entry = site_to_laqn_site_entry(site)
                session.add(site_entry)

            else:
                site_data = site_info_query.filter(
                    laqn_sites.SiteCode == site["@SiteCode"]).first()

                date_site_closed = site_data.DateClosed

                if ((site["@DateClosed"] != "") and date_site_closed is None):

                    logging.info("Site %s has closed. Updating %s", green(
                        site["@SiteCode"]), green(laqn_sites.__tablename__))

                    site_data.DateClosed = site["@DateClosed"]

        logging.info("Committing any changes to database table %s",
                     green(laqn_sites.__tablename__))
        session.commit()


def check_laqn_entry_exists(session, reading):
    """
    Check if an laqn entry already exists in the database
    """
    criteria = and_(laqn_reading.SiteCode == reading.SiteCode,
                    laqn_reading.SpeciesCode == reading.SpeciesCode,
                    laqn_reading.MeasurementDateGMT == reading.MeasurementDateGMT)

    ret = session.query(exists().where(criteria)).scalar()

    if ret:
        query = session.query(laqn_reading).filter(criteria)
    else:
        query = None

    return ret, query


def add_reading_entries(session, site_code, readings):
    """
    Pass a list of dictionaries for readings and put them into db
    """
    all_reading_entries = []
    for r in readings:

        r["@SiteCode"] = site_code

        # Check the entry doesn"t exist in the database
        new_laqn_reading_entry = laqn_reading_entry(r)

        if not check_laqn_entry_exists(session, new_laqn_reading_entry)[0]:
            all_reading_entries.append(new_laqn_reading_entry)
        else:
            logging.debug(
                "Entry sitecode: {}, measurementDateGMT: {}, speciedCode: {} exists in database".format(green(site_code), green(r['@MeasurementDateGMT']), green(r['@SpeciesCode'])))

    session.add_all(all_reading_entries)


def datetime_floor(dtime):
    """
    Set the time to midnight for a given datetime
    """
    return datetime.combine(dtime, datetime.min.time())


def get_data_range(site, start_date, end_date):
    """
    Get the dates that data is available for a site between start_date and end_date
    If no data is available between these dates returns None
    """

    if not start_date:
        get_data_from = datetime_floor(site.DateOpened)
    else:
        get_data_from = max(
            [datetime_floor(site.DateOpened), datetime_floor(str_to_datetime(start_date))])

    if not end_date:
        get_data_to = min(
            [datetime_floor(datetime.today()), datetime_floor(site.DateClosed)])

    else:
        if not site.DateClosed:
            get_data_to = datetime_floor(str_to_datetime(end_date))
        else:
            # Site is closed to get data until that point
            get_data_to = min(
                [datetime_floor(str_to_datetime(end_date)),
                 datetime_floor(site.DateClosed)]
            )

    delta = get_data_to - get_data_from  # Number of days available for a site

    if delta.days < 0:
        return None
    return (get_data_from, get_data_to)


def update_reading_table(session, start_date=None, end_date=None, force=False):
    """
    Add missing reading data to the database

    start date: date to get data from (yyyy-mm-dd). If None will get from site opening date.
    end_date: date to get data to. If None will get till today, or when site closed.
    """

    logging.info("Attempting to download data between %s and %s",
                 green(start_date), green(end_date))

    site_info_query = session.query(laqn_sites)
    laqn_readings_query = session.query(laqn_reading)

    for site in site_info_query:

        site_query = laqn_readings_query.filter(
            laqn_reading.SiteCode == site.SiteCode)

        # What dates can we get data for
        date_from_to = get_data_range(site, start_date, end_date)

        if date_from_to is None:
            logging.info("No data is available for site %s between %s and %s", red(
                site.SiteCode), red(start_date), red(end_date))
            continue

        # List of dates to get data for
        delta = date_from_to[1] - date_from_to[0]
        date_range = [date_from_to[0] + timedelta(i) for i in range(delta.days + 1)]

        for i, date in enumerate(date_range):

            # Query readings in the database for this date ignoring species
            readings_in_db = site_query.distinct(laqn_reading.MeasurementDateGMT).filter(
                and_(laqn_reading.MeasurementDateGMT >= date, laqn_reading.MeasurementDateGMT < date + days(1))).all()

            # If no database entries for that date or the date trying to get data for is today, or the force flag is set to true then try and get data.
            # If the date is not today or yesterday and the force flag is not
            # True assumes the data is in the database and does not attempt to
            # get it
            if (len(readings_in_db) == 0) or (
                    (datetime.today().date() - date.date()).days < 2) or (force):

                logging.info("Getting data for site %s for date: %s", red(
                    site.SiteCode), red(date_range[i].date()))

                d = get_site_reading(site.SiteCode, str(
                    date.date()), str((date + days(1)).date()))

                if d is not None:
                    add_reading_entries(session, site.SiteCode, d)

                else:
                    logging.info("Request for data for {} between dates {} and {} failed".format(
                        site.SiteCode, date, (date + days(1)).date()))

            else:

                logging.info("Data already in db for site {} for date: {}. Not requesting data. To request data include the -f flag ".format(
                    green(site.SiteCode), green(date_range[i].date())))

        session.commit()


def load_db_info():
    """
    Check file system is accessable from docker and return database login info
    """

    mount_dir = '/secrets/'
    local_dir = './terraform/.secrets/'
    secret_file = '.laqn_secret.json'

    # Check if the following directories exist
    check_secrets_mount = os.path.isdir(mount_dir)
    check_local_dir = os.path.isdir(local_dir)

    secret_fname = None
    if check_secrets_mount:
        logging.info("{} is mounted".format(mount_dir))
        secret_fname = os.path.join(mount_dir, secret_file)

    elif check_local_dir:
        logging.info("{} exists locally".format(check_local_dir))
        secret_fname = os.path.join(local_dir, secret_file)

    else:
        raise FileNotFoundError(
            "Database secrets could not be found. Check that either {} is mounted or {} exists locally".format(mount_dir, local_dir))

    try:
        with open(secret_fname) as f:
            data = json.load(f)
           
        logging.info("Database connection information loaded")

    except FileNotFoundError:
        logging.error(
            "Database secrets could not be found. Ensure secret_file exists")
        raise FileNotFoundError

    return data


def process_args():

    # Read command line arguments
    parser = argparse.ArgumentParser(
        description='Get LAQN data from the KCL API')

    parser.add_argument("-e", "--end", type=str, default="today",
                        help="The last date to get data for in international standard date notation (YYYY-MM-DD)")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-n", "--ndays", type=int, default=2,
                       help="The number of days to request data for. ndays=1 will get today (from midnight)")
    group.add_argument("-s", "--start", type=str,
                       help="The first date to get data for in international standard date notation (YYYY-MM-DD). If --ndays is provided this argument is ignored. Will get data from midnight")
    parser.add_argument('-f', "--force", action="store_true",
                        help="Attempt to write to database even if data for that date is already in database. This is done for todays date regardless of whether -f is given")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Set the logger level to debug")
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

    logging.info("LAQN data. Request Start date = {} to: End date = {}. Data is collected from {} on the start date until {} on the end date. Force is set {} - when True will try to write each entry to the database".format(
        red(args.start), red(args.end), green("00:00:00"), green("23:59:59"), red(args.force)))

    return args.start, args.end, args.force


def main():

    start_date, end_date, force = process_args()

    db_info = load_db_info()

    logging.info("Starting laqn_database script")
    logging.info("Has internet connection: %s", connected_to_internet())

    # Connect to the database
    host = db_info["host"]
    port = db_info["port"]
    dbname = db_info["db_name"]
    user = db_info["username"]
    db_password = db_info["password"]

    connection_string = create_connection_string(host=host,
                                                 port=port,
                                                 dbname=dbname,
                                                 user=user,
                                                 password=db_password)

    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Update the laqn_sites database table
    update_site_list_table(session)

    # Update data in laqn reading table
    today = datetime.today().date()

    # Update data in laqn reading table
    update_reading_table(session, start_date=str(start_date),
                         end_date=str(end_date), force=force)

    logging.info("LAQN jobs finished")


if __name__ == '__main__':

    main()

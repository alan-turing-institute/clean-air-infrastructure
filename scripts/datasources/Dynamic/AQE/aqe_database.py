"""
Get data from the LAQN network via the API maintained by Kings Colleage London (https://www.londonair.org.uk/Londonair/API/)
"""
import argparse
import requests
import os
import logging
import termcolor
import json
from sqlalchemy import Column, Integer, String, create_engine, exists, and_
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.sql import text
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pdb

from datetime import datetime, timedelta
from io import BytesIO, StringIO
from xml.dom import minidom
import csv

def days(d):
    "Time delta in days"
    return timedelta(days = d)

def emp1(text):
    return termcolor.colored(text, 'green')


def emp2(text):
    return termcolor.colored(text, 'red')


def connected_to_internet(url='http://www.google.com/', timeout=5):    
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False


def site_list_xml_to_list(dom_object):
    """ 
    Covert dom object to a list of dictionaries. Each dictionary is an site containing site information"""

    return [dict(s.attributes.items()) for s in dom_object.getElementsByTagName("Site")]


def get_site_info():
    """
    Get info on all aqe sites    
    
    Returns: A dom object (https://docs.python.org/3/library/xml.dom.minidom.html#module-xml.dom.minidom)
    """    

    r = requests.get(
        'http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site', timeout=5.)

    if r.status_code == 200:
        dom1 = minidom.parse(BytesIO(r.content))
        return site_list_xml_to_list(dom1)



def get_site_reading(sitecode, start_date, end_date):
    """
    Request data for a given {sitecode} between {start_date} and {end_date}. 
    Dates given in %yyyy-mm-dd%
    """

    r = requests.get(
       'http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/{}/{}/{}'.format(sitecode, start_date, end_date))


    if r.status_code == 200:

        return process_site_reading(sitecode, r.content)



def process_site_reading(sitecode, content):
    """
    Process a site reading. 
    Returns a list of dictionaires
    """


    reader = csv.reader(StringIO(content.decode()))

    # Get the header and the content
    header = reader.__next__()
    readings = [row for row in reader]

    
   
    species = [s.split(": ")[1].split(" ")[0] for s in header[1:]]

    readings_processed = []

    for r in readings:
        
        for s in range(len(r) - 1):
            
            reading_dict = dict(SiteCode = sitecode,
                                SpeciesCode = species[s],
                                MeasurementDateGMT = r[0],
                                Value = r[s])

            readings_processed.append(reading_dict)

    return readings_processed




# def drop_duplicates(data):
#     "If the data from the data contains duplicates then drop them"

#     drop_list = [dict(t) for t in {tuple(d.items()) for d in data}]

#     if len(drop_list) != len(data):
#         logging.warning("Dropped data")
#         return drop_list

#     else:
#         return data


def dict_clean(dictionary):

    for key in dictionary.keys():
        if dictionary[key] == '':
            dictionary[key] = None

    return dictionary


# def str_to_datetime(date_str):
#     return datetime.strptime(date_str, '%Y-%m-%d')

# Database functions

# DataBase specification
Base = declarative_base()
class aqe_sites(Base):
    __tablename__ = 'aqe_sites'
    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SiteName = Column(String(), nullable = False)
    SiteType = Column(String(20), nullable=False)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)

    SiteLink =  Column(String)
    DataManager = Column(String)     
    geom = Column(Geometry(geometry_type = "POINT", srid = 4326, dimension = 2, spatial_index=True))


class aqe_reading(Base):
    __tablename__ = 'laqn_readings'

    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def create_connection_string(host, port, dbname, user, password, ssl_mode='require'):
    "Create a postgres connection string"
    connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(
        user, password, host, port, dbname)

    return connection_string


def site_to_aqe_site_entry(site):
    "Create an laqn_sites entry"

    site = dict_clean(site)

    # Hack to make geom = NULL if longitude and latitude dont exist
    if (site['Longitude'] == None) or (site['Latitude'] == None):
        out = aqe_sites(SiteCode=site['SiteCode'],       
                    SiteName=site['SiteName'],
                    SiteType=site['SiteType'],                    
                    Latitude=site['Latitude'],
                    Longitude=site['Longitude'],
                    DateOpened=site['DateOpened'],
                    DateClosed=site['DateClosed'],           
                    SiteLink=site['SiteLink'],
                    DataManager=site['DataManager']
                    )
    else:    
        geom_string = 'SRID=4326;POINT({} {})'.format(site['Longitude'], site['Latitude'])    
        out = aqe_sites(SiteCode=site['SiteCode'],       
                    SiteName=site['SiteName'],
                    SiteType=site['SiteType'],                    
                    Latitude=site['Latitude'],
                    Longitude=site['Longitude'],
                    DateOpened=site['DateOpened'],
                    DateClosed=site['DateClosed'],           
                    SiteLink=site['SiteLink'],
                    DataManager=site['DataManager'], 
                    geom = geom_string  
                    )
    return out


# def laqn_reading_entry(reading):
#     "Create an laqn_read entry"
#     reading = dict_clean(reading)

#     return laqn_reading(SiteCode=reading['@SiteCode'],
#                         SpeciesCode=reading['@SpeciesCode'],
#                         MeasurementDateGMT=reading['@MeasurementDateGMT'],
#                         Value=reading['@Value'])


def create_sitelist(site_info):
    "Return a list of laqn_site objects"

    all_sites = []

    for site in site_info:
        all_sites.append(
            site_to_aqe_site_entry(site)
        )
    return all_sites


def update_site_list_table(session):
    "Update the site info"

    logging.info("Requesting site info from {}".format(emp1("AQE API")))
    site_info = get_site_info()

    # Query site_info entires
    site_info_query = session.query(aqe_sites)

    # Check if database table is empty
    if len(site_info_query.all()) == 0:
        logging.info("Database is empty. Inserting all entries")
        site_db_entries = create_sitelist(site_info)
        session.add_all(site_db_entries)
        session.commit()

    # If not empty check it has latest information
    else:
        # Check if site exists and database is up to date
        logging.info("Crosscheck entries in database table {}".format(
            emp1(aqe_sites.__tablename__)))

        for site in site_info:
            # Check if site exists
            site_exists = session.query(exists().where(
                aqe_sites.SiteCode == site['SiteCode'])).scalar()

            if not site_exists:
                logging.info("Site {} not in {}. Creating entry".format(emp1(site['SiteCode']),
                                                                        emp1(aqe_sites.__tablename__)))
                site_entry = site_to_aqe_site_entry(site)
                session.add(site_entry)                
            else:

                site_data = site_info_query.filter(
                    aqe_sites.SiteCode == site['SiteCode']).first()

                date_site_closed = site_data.DateClosed
                if ((site['DateClosed'] != "") and date_site_closed is None):

                    logging.info("Site {} has closed. Updating {}".format(emp1(site['SiteCode']),
                                                                          emp1(aqe_sites.__tablename__)))
                    site_data.DateClosed = site['DateClosed']        
        logging.info("Committing any changes to database table {}".format(
            emp1(aqe_sites.__tablename__)))
        session.commit()


# def check_laqn_entry_exists(session, reading):
#     "Check if an laqn entry already exists in the database"
#     criteria = and_(laqn_reading.SiteCode == reading.SiteCode, laqn_reading.SpeciesCode ==
#                     reading.SpeciesCode, laqn_reading.MeasurementDateGMT == reading.MeasurementDateGMT)

#     ret = session.query(exists().where(criteria)).scalar()

#     if ret:
#         query = session.query(laqn_reading).filter(criteria)
#     else:
#         query = None

#     return ret, query


# def add_reading_entries(session, site_code, readings):
#     "Pass a list of dictionaries for readings and put them into db"

#     all_reading_entries = []
#     for r in readings:

#         r['@SiteCode'] = site_code

#         # Check the entry doesn't exist in the database
#         new_laqn_reading_entry = laqn_reading_entry(r)

#         if not check_laqn_entry_exists(session, new_laqn_reading_entry)[0]:
#             all_reading_entries.append(new_laqn_reading_entry)
#         else:
#             logging.debug(
#                 "Entry sitecode: {}, measurementDateGMT: {}, speciedCode: {} exists in database".format(emp2(site_code), emp2(r['@MeasurementDateGMT']), emp2(r['@SpeciesCode'])))

#     session.add_all(all_reading_entries)


# def datetime_floor(dtime):
#     "Set the time to midnight for a given datetime"
#     return datetime.combine(
#         dtime, datetime.min.time())


# def get_data_range(site, start_date, end_date):
#     """Get the dates that data is available for a site between start_date and end_date
#     If no data is available between these dates returns None
#     """

#     if start_date is None:
#         get_data_from = datetime_floor(site.DateOpened)
#     else:
#         get_data_from = max(
#             [datetime_floor(site.DateOpened), datetime_floor(str_to_datetime(start_date))])

#     if end_date is None:
#         get_data_to = min(
#             [datetime_floor(datetime.today()), datetime_floor(site.DateClosed)])

#     else:
#         if site.DateClosed is None:
#             get_data_to = datetime_floor(str_to_datetime(end_date))
#         else:
#             # Site is closed to get data until that point
#             get_data_to = min(
#                 [datetime_floor(str_to_datetime(end_date)),
#                     datetime_floor(site.DateClosed)]
#             )

#     delta = get_data_to - get_data_from  # Number of days available for a site

#     if delta.days < 0:
#         return None
#     else:
#         return (get_data_from, get_data_to)


def update_reading_table(session, start_date=None, end_date=None, force = False):
    """
    Add missing reading data to the database

    start date: date to get data from (yyyy-mm-dd). If None will get from site opening date.
    end_date: date to get data to. If None will get till today, or when site closed.
    """

    logging.info("Attempting to download data between {} and {}".format(emp1(start_date), emp1(end_date)))

    site_info_query = session.query(aqe_sites)
    aqe_readings_query = session.query(aqe_reading)

    for site in site_info_query:

        site_query = aqe_readings_query.filter(
            aqe_reading.SiteCode == site.SiteCode)

#         # What dates can we get data for
#         date_from_to = get_data_range(site, start_date, end_date)

#         if date_from_to is None:
#             logging.info("No data is available for site {} between {} and {}".format(
#                 emp2(site.SiteCode), emp2(start_date), emp2(end_date)))
#             continue

#         # List of dates to get data for
#         delta = date_from_to[1] - date_from_to[0]
#         date_range = [date_from_to[0] +
#                       timedelta(i) for i in range(delta.days+1)]

#         for i, date in enumerate(date_range):

#             # Query readings in the database for this date ignoring species
#             readings_in_db = site_query.distinct(laqn_reading.MeasurementDateGMT).filter(
#                 and_(laqn_reading.MeasurementDateGMT >= date, laqn_reading.MeasurementDateGMT < date + days(1))).all()

#             # If no database entries for that date or the date trying to get data for is today, or the force flag is set to true then try and get data. 
#             # If the date is not today or yesterday and the force flag is not True assumes the data is in the database and does not attempt to get it
#             if (len(readings_in_db) == 0) or ( (datetime.today().date() - date.date() ).days < 2) or (force):

#                 logging.info("Getting data for site {} for date: {}".format(
#                     emp2(site.SiteCode), emp2(date_range[i].date())))

#                 d = get_site_reading(site.SiteCode, str(
#                     date.date()), str((date + days(1)).date()))

#                 if d is not None:
#                     add_reading_entries(session, site.SiteCode, d)

#                 else:
#                     logging.info("Request for data for {} between dates {} and {} failed".format(
#                         site.SiteCode, date, (date + days(1)).date()))
          
#             else:

#                 logging.info("Data already in db for site {} for date: {}. Not requesting data. To request data include the -f flag ".format(
#                 emp2(site.SiteCode), emp2(date_range[i].date())))     

#         session.commit()


def load_db_info():
    "Check file system is accessable from docker and return database login info"
  

    mount_dir = '/secrets/aqecred/'
    local_dir = './terraform/.secrets/'
    secret_file = '.aqe_secret.json'

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
        raise FileNotFoundError("Database secrets could not be found. Check that either {} is mounted or {} exists locally".format(mount_dir, local_dir))

    
    try:
        with open(secret_fname) as f:
            data = json.load(f)        
        logging.info("Database connection information loaded")

    except FileNotFoundError:
        logging.error("Database secrets could not be found. Ensure secret_file exists")
        raise FileNotFoundError
  
    return data


def process_args():

    # Read command line arguments
    parser = argparse.ArgumentParser(description='Get AQE data')

    parser.add_argument("-e", "--end", type=str, default="today", help="The last date to get data for in international standard date notation (YYYY-MM-DD)")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-n", "--ndays", type=int, default=2, help="The number of days to request data for. ndays=1 will get today (from midnight)")
    group.add_argument("-s", "--start", type=str, help="The first date to get data for in international standard date notation (YYYY-MM-DD). If --ndays is provided this argument is ignored. Will get data from midnight")  
    parser.add_argument('-f', "--force", action="store_true", help="Attempt to write to database even if data for that date is already in database. This is done for todays date regardless of whether -f is given")
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
            raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")
        args.start = args.end - days(args.ndays - 1)
    else:
        args.start = datetime.strptime(args.start, "%Y-%m-%d").date()

    logging.info("LAQN data. Request Start date = {} to: End date = {}. Data is collected from {} on the start date until {} on the end date. Force is set {} - when True will try to write each entry to the database".format(emp1(args.start), emp1(args.end), emp2("00:00:00"), emp2("23:59:59"), emp1(args.force)))

    return args.start, args.end, args.force

def main():

    start_date, end_date, force = process_args()

    db_info = load_db_info()

    logging.info("Starting laqn_database script")
    logging.info("Has internet connection: {}".format(connected_to_internet()))

    # Connect to the database
    host = db_info['host']
    port = db_info['port']
    dbname = db_info['db_name']
    user = db_info['username']
    ssl_mode = db_info['ssl_mode']
    db_password = db_info['password']

    connection_string = create_connection_string(host=host,
                                                 port=port,
                                                 dbname=dbname,
                                                 user=user,
                                                 password=db_password,
                                                 ssl_mode=ssl_mode)

    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
 

    # Update the aqe_sites database table
    update_site_list_table(session)


#     # # Update data in laqn reading table
#     update_reading_table(session, start_date = str(start_date),
#                          end_date = str(end_date), force = force)

    logging.info("AQE jobs finished")


if __name__ == '__main__':
    
    
    # main()
    pass


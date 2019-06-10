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


logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s",
                    datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)


ONE_DAY = timedelta(days=1)

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


def get_site_info():
    "Get info on all laqn sites"
    
    r = requests.get(
        'http://api.erg.kcl.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json', timeout=5.)

    if r.status_code == 200:
        site_list = r.json()['Sites']['Site']

        return site_list


def get_site_reading(sitecode, start_date, end_date):
    "Request data for a given {sitecode} between {start_date} and {end_date}. Dates given in %yyyy-mm-dd%"

    r = requests.get(
        'http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json'.format(sitecode,
                                                                                                        start_date, end_date))

    if r.status_code == 200:

        data = r.json()['AirQualityData']['Data']

        return drop_duplicates(data)


def drop_duplicates(data):
    "If the data from the kcl api contains duplicates then drop them"

    drop_list = [dict(t) for t in {tuple(d.items()) for d in data}]

    if len(drop_list) != len(data):
        logging.warning("Dropped data")
        return drop_list

    else:
        return data


def dict_clean(dictionary):

    for key in dictionary.keys():
        if dictionary[key] == '':
            dictionary[key] = None

    return dictionary


def str_to_datetime(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')

# Database functions

# DataBase specification
Base = declarative_base()
class laqn_sites(Base):
    __tablename__ = 'laqn_sites'

    SiteCode = Column(String(4), primary_key=True, nullable=False)
    la_id = Column(Integer, nullable=False)
    SiteType = Column(String(20), nullable=False)
    os_grid_x = Column(DOUBLE_PRECISION)
    os_grid_y = Column(DOUBLE_PRECISION)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)
    geom = Column(Geometry(geometry_type = "POINT", srid = 4326, dimension = 2, spatial_index=True))


class laqn_reading(Base):
    __tablename__ = 'laqn_readings'

    SiteCode = Column(String(4), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def create_connection_string(host, port, dbname, user, password, ssl_mode='require'):
    "Create a postgres connection string"
    connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(
        user, password, host, port, dbname)

    return connection_string


def site_to_laqn_site_entry(site):
    "Create an laqn_sites entry"
    site_info = dict_clean(site)


    # Hack to make geom = NULL if longitude and latitude dont exist
    if (site['@Longitude'] == None) or (site['@Latitude'] == None):
        out = laqn_sites(SiteCode=site['@SiteCode'],
                    la_id=site['@LocalAuthorityCode'],
                    SiteType=site['@SiteType'],
                    Latitude=site['@Latitude'],
                    Longitude=site['@Longitude'],
                    DateOpened=site['@DateOpened'],
                    DateClosed=site['@DateClosed']            
                    )

    else:    
        geom_string = 'SRID=4326;POINT({} {})'.format(site['@Longitude'], site['@Latitude'])    
        out = laqn_sites(SiteCode=site['@SiteCode'],
                    la_id=site['@LocalAuthorityCode'],
                    SiteType=site['@SiteType'],
                    Latitude=site['@Latitude'],
                    Longitude=site['@Longitude'],
                    DateOpened=site['@DateOpened'],
                    DateClosed=site['@DateClosed'] ,
                    geom = geom_string          
                    ) 

    return out


def laqn_reading_entry(reading):
    "Create an laqn_read entry"
    reading = dict_clean(reading)

    return laqn_reading(SiteCode=reading['@SiteCode'],
                        SpeciesCode=reading['@SpeciesCode'],
                        MeasurementDateGMT=reading['@MeasurementDateGMT'],
                        Value=reading['@Value'])


def create_sitelist(site_info):
    "Return a list of laqn_site objects"

    all_sites = []

    for site in site_info:

        all_sites.append(
            site_to_laqn_site_entry(site)
        )

    return all_sites


def update_site_list_table(session):
    "Update the site info"

    # # Update site info
    logging.info("Requesting site info from {}".format(emp1("kcl API")))
    site_info = get_site_info()

    # Query site_info entires
    site_info_query = session.query(laqn_sites)

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
            emp1(laqn_sites.__tablename__)))

        for site in site_info:

            # Check if site exists
            site_exists = session.query(exists().where(
                laqn_sites.SiteCode == site['@SiteCode'])).scalar()

            if not site_exists:
                logging.info("Site {} not in {}. Creating entry".format(emp1(site['@SiteCode']),
                                                                        emp1(laqn_sites.__tablename__)))
                site_entry = site_to_laqn_site_entry(site)
                session.add(site_entry)

                

            else:

                site_data = site_info_query.filter(
                    laqn_sites.SiteCode == site['@SiteCode']).first()

                date_site_closed = site_data.DateClosed

                if ((site['@DateClosed'] != "") and date_site_closed is None):

                    logging.info("Site {} has closed. Updating {}".format(emp1(site['@SiteCode']),
                                                                          emp1(laqn_sites.__tablename__)))

                    site_data.DateClosed = site['@DateClosed']
        
        logging.info("Committing any changes to database table {}".format(
            emp1(laqn_sites.__tablename__)))
        session.commit()


def check_laqn_entry_exists(session, reading):
    "Check if an laqn entry already exists in the database"
    criteria = and_(laqn_reading.SiteCode == reading.SiteCode, laqn_reading.SpeciesCode ==
                    reading.SpeciesCode, laqn_reading.MeasurementDateGMT == reading.MeasurementDateGMT)

    ret = session.query(exists().where(criteria)).scalar()

    if ret:
        query = session.query(laqn_reading).filter(criteria)
    else:
        query = None

    return ret, query


def add_reading_entries(session, site_code, readings):
    "Pass a list of dictionaries for readings and put them into db"
    all_reading_entries = []
    for r in readings:

        r['@SiteCode'] = site_code

        # Check the entry doesn't exist in the database
        new_laqn_reading_entry = laqn_reading_entry(r)

        if not check_laqn_entry_exists(session, new_laqn_reading_entry)[0]:
            all_reading_entries.append(new_laqn_reading_entry)
        else:
            logging.warning(
                "Entry for {} exists in database".format(emp2(site_code)))

    session.add_all(all_reading_entries)


def datetime_floor(dtime):
    "Set the time to midnight for a given datetime"
    return datetime.combine(
        dtime, datetime.min.time())


def get_data_range(site, start_date, end_date):
    """Get the dates that data is available for a site between start_date and end_date
    If no data is available between these dates returns None
    """

    if start_date is None:
        get_data_from = datetime_floor(site.DateOpened)
    else:
        get_data_from = max(
            [datetime_floor(site.DateOpened), datetime_floor(str_to_datetime(start_date))])

    if end_date is None:
        get_data_to = min(
            [datetime_floor(datetime.today()), datetime_floor(site.DateClosed)])

    else:
        if site.DateClosed is None:
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
    else:
        return (get_data_from, get_data_to)


def update_reading_table(session, start_date=None, end_date=None):
    """
    Add missing reading data to the database

    start date: date to get data from (yyyy-mm-dd). If None will get from site opening date.
    end_date: date to get data to. If None will get till today, or when site closed.
    """

    logging.info("Attempting to download data between {} and {}".format(emp1(start_date), emp1(end_date)))

    site_info_query = session.query(laqn_sites)
    laqn_readings_query = session.query(laqn_reading)

    for site in site_info_query:

        site_query = laqn_readings_query.filter(
            laqn_reading.SiteCode == site.SiteCode)

        # What dates can we get data for
        date_from_to = get_data_range(site, start_date, end_date)

        if date_from_to is None:
            logging.info("No data is available for site {} between {} and {}".format(
                emp2(site.SiteCode), emp2(start_date), emp2(end_date)))
            continue

        # List of dates to get data for
        delta = date_from_to[1] - date_from_to[0]
        date_range = [date_from_to[0] +
                      timedelta(i) for i in range(delta.days+1)]

        for i, date in enumerate(date_range):

            # Query readings in the database for this date ignoring species
            readings_in_db = site_query.distinct(laqn_reading.MeasurementDateGMT).filter(
                and_(laqn_reading.MeasurementDateGMT >= date, laqn_reading.MeasurementDateGMT < date + ONE_DAY)).all()

            # If no database entries for that date try to get them
            if len(readings_in_db) == 0:

                logging.info("Getting data for site {} for date: {}".format(
                    emp2(site.SiteCode), emp2(date_range[i].date())))

                d = get_site_reading(site.SiteCode, str(
                    date.date()), str((date + ONE_DAY).date()))

                if d is not None:
                    add_reading_entries(session, site.SiteCode, d)

                else:
                    logging.warning("Request for data for {} between dates {} and {} failed".format(
                        site.SiteCode, date, (date + ONE_DAY).date()))

            else:
                logging.info("Data already in db for site {} for date: {}".format(
                    emp2(site.SiteCode), emp2(date_range[i].date())))

        session.commit()


def load_db_info():
    "Check file system is accessable from docker and return database login info"
    import glob

    check_secrets_exist = os.path.isdir('/secrets/laqncred/')

    print(glob.glob('/secrets/laqncred/', recursive=True))

    if not check_secrets_exist:
        logging.error("/secrets folder does not exist")
        raise FileNotFoundError("/secrets folder does not exist")

    try:
        with open("/secrets/laqncred/.laqn_secret.json") as f:
            data = json.load(f)        
        logging.info("/secrets folder found. Database connection information loaded")

    except FileNotFoundError:
        logging.error("/secrets folder not found. Check docker bindmount")
        raise FileNotFoundError

    return data

def install_gis(engine):
    logging.info("Ensuring postgis extention installed")
    connection = engine.connect()
    connection.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    connection.close()

def main():

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
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Ensure GIS installed
    install_gis(engine)

    # DROP the table
    # laqn_sites.__table__.drop(engine)
    # laqn_readings.__table__.drop(engine)

    # # Update the laqn_sites database table
    update_site_list_table(session)


    # # Update data in laqn reading table
    today =  datetime.today().date()
    update_reading_table(session, start_date = str(today - ONE_DAY),
                         end_date = str(today))

    logging.info("LAQN jobs finished")

if __name__ == '__main__':
    
    main()


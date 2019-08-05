"""
Get data from the AQE network via the API
"""
import csv
import logging
import requests
from .database_management import database_management as dbm
from datetime import timedelta, datetime
from geoalchemy2 import Geometry
from io import BytesIO, StringIO
from sqlalchemy import Column, String, create_engine, exists, and_
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from xml.dom import minidom

logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)


def site_list_xml_to_list(dom_object):
    """Convert DOM object to a list of dictionaries. Each dictionary is an site containing site information"""
    return [dict(s.attributes.items()) for s in dom_object.getElementsByTagName("Site")]


def get_site_info():
    """
    Get info on all aqe sites
    Returns: A DOM object (https://docs.python.org/3/library/xml.dom.minidom.html#module-xml.dom.minidom)
    """
    r = requests.get("http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site", timeout=5.0)

    if r.status_code == 200:
        dom1 = minidom.parse(BytesIO(r.content))
        return site_list_xml_to_list(dom1)
    return None


def get_site_reading(sitecode, start_date, end_date):
    """
    Request data for a given {sitecode} between {start_date} and {end_date}.
    Dates given in %yyyy-mm-dd%
    """
    r = requests.get("http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/{}/{}/{}".format(
                     sitecode, start_date, end_date))

    if r.status_code == 200:
        return process_site_reading(sitecode, r.content)
    return None


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
            reading_dict = {'@SiteCode': sitecode,
                            '@SpeciesCode': species[s],
                            '@MeasurementDateGMT': r[0],
                            '@Value': r[s + 1]}
            readings_processed.append(reading_dict)
    return readings_processed


# DataBase specification
Base = declarative_base()


class aqe_sites(Base):
    __tablename__ = 'aqe_sites'
    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SiteName = Column(String(), nullable=False)
    SiteType = Column(String(20), nullable=False)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)

    SiteLink = Column(String)
    DataManager = Column(String)
    geom = Column(Geometry(geometry_type="POINT", srid=4326,
                           dimension=2, spatial_index=True))


class aqe_reading(Base):
    __tablename__ = 'aqe_readings'

    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def site_to_aqe_site_entry(site):
    """Create an aqe_sites entry"""
    site = dbm.dict_clean(site)

    # Hack to make geom = NULL if longitude and latitude dont exist
    if (site['Longitude'] is None) or (site['Latitude'] is None):
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
        geom_string = 'SRID=4326;POINT({} {})'.format(
            site['Longitude'], site['Latitude'])
        out = aqe_sites(SiteCode=site['SiteCode'],
                        SiteName=site['SiteName'],
                        SiteType=site['SiteType'],
                        Latitude=site['Latitude'],
                        Longitude=site['Longitude'],
                        DateOpened=site['DateOpened'],
                        DateClosed=site['DateClosed'],
                        SiteLink=site['SiteLink'],
                        DataManager=site['DataManager'],
                        geom=geom_string
                        )
    return out


def aqe_reading_entry(reading):
    """Create an aqe_read entry"""
    reading = dbm.dict_clean(reading)
    return aqe_reading(SiteCode=reading['@SiteCode'],
                       SpeciesCode=reading['@SpeciesCode'],
                       MeasurementDateGMT=reading['@MeasurementDateGMT'],
                       Value=reading['@Value'])


def create_sitelist(site_info):
    """Return a list of aqe_site objects"""
    return [site_to_aqe_site_entry(site) for site in site_info]


def update_site_list_table(session):
    """Update the site info"""
    logging.info("Requesting site info from %s", dbm.green("AQE API"))
    site_info = get_site_info()

    # Query site_info entires
    site_info_query = session.query(aqe_sites)

    # Check if database table is empty
    if not site_info_query.all():
        logging.info("Database is empty. Inserting all entries")
        site_db_entries = create_sitelist(site_info)
        session.add_all(site_db_entries)
        session.commit()

    # If not empty check it has latest information
    else:
        # Check if site exists and database is up to date
        logging.info("Crosscheck entries in database table %s", dbm.green(aqe_sites.__tablename__))

        for site in site_info:
            # Check if site exists
            site_exists = session.query(exists().where(aqe_sites.SiteCode == site['SiteCode'])).scalar()

            if not site_exists:
                logging.info("Site %s not in %s. Creating entry",
                             dbm.green(site['SiteCode']),
                             dbm.green(aqe_sites.__tablename__))
                site_entry = site_to_aqe_site_entry(site)
                session.add(site_entry)
            else:

                site_data = site_info_query.filter(aqe_sites.SiteCode == site['SiteCode']).first()

                date_site_closed = site_data.DateClosed
                if ((site['DateClosed'] != "") and date_site_closed is None):
                    logging.info("Site %s has closed. Updating %s",
                                 dbm.green(site['SiteCode']),
                                 dbm.green(aqe_sites.__tablename__))
                    site_data.DateClosed = site['DateClosed']
        logging.info("Committing any changes to database table %s", dbm.green(aqe_sites.__tablename__))
        session.commit()


def check_aqe_entry_exists(session, reading):
    "Check if an aqe entry already exists in the database"
    criteria = and_(aqe_reading.SiteCode == reading.SiteCode,
                    aqe_reading.SpeciesCode == reading.SpeciesCode,
                    aqe_reading.MeasurementDateGMT == reading.MeasurementDateGMT)

    ret = session.query(exists().where(criteria)).scalar()

    if ret:
        query = session.query(aqe_reading).filter(criteria)
    else:
        query = None

    return ret, query


def add_reading_entries(session, site_code, readings):
    """Pass a list of dictionaries for readings and put them into db"""
    all_reading_entries = []
    for r in readings:
        # Check the entry doesn't exist in the database
        new_aqe_reading_entry = aqe_reading_entry(r)

        if not check_aqe_entry_exists(session, new_aqe_reading_entry)[0]:
            all_reading_entries.append(new_aqe_reading_entry)
        else:
            logging.debug("Entry sitecode: %s, measurementDateGMT: %s, speciedCode: %s exists in database",
                          dbm.red(site_code),
                          dbm.red(r['@MeasurementDateGMT']),
                          dbm.red(r['@SpeciesCode']))

    session.add_all(all_reading_entries)


def update_reading_table(session, start_date=None, end_date=None, force=False):
    """
    Add missing reading data to the database

    start date: date to get data from (yyyy-mm-dd). If None will get from site opening date.
    end_date: date to get data to. If None will get till today, or when site closed.
    """

    logging.info("Attempting to download data between %s and %s", dbm.green(start_date), dbm.green(end_date))

    site_info_query = session.query(aqe_sites)
    aqe_readings_query = session.query(aqe_reading)

    for site in site_info_query:
        site_query = aqe_readings_query.filter(aqe_reading.SiteCode == site.SiteCode)

        # What dates can we get data for
        date_from_to = dbm.get_data_range(site, start_date, end_date)

        if date_from_to is None:
            logging.info("No data is available for site %s between %s and %s",
                         dbm.red(site.SiteCode), dbm.red(start_date), dbm.red(end_date))
            continue

        # List of dates to get data for
        delta = date_from_to[1] - date_from_to[0]
        date_range = [date_from_to[0] + timedelta(i) for i in range(delta.days + 1)]

        for i, date in enumerate(date_range):
            # Query readings in the database for this date ignoring species
            readings_in_db = site_query.distinct(aqe_reading.MeasurementDateGMT).filter(
                and_(aqe_reading.MeasurementDateGMT >= date, aqe_reading.MeasurementDateGMT < date + dbm.days(1))).all()

            # If no database entries for that date
            # OR the date trying to get data for is today
            # OR the force flag is set to true then try to get data.
            #
            # If the date is not today or yesterday and the force flag is not True we assume the data is in the database
            # and do not attempt to get it
            if readings_in_db or ((datetime.today().date() - date.date()).days < 2) or (force):
                logging.info("Getting data for site %s for date: %s",
                             dbm.red(site.SiteCode),
                             dbm.red(date_range[i].date()))

                d = get_site_reading(site.SiteCode, str(date.date()), str((date + dbm.days(1)).date()))

                if d is not None:
                    add_reading_entries(session, site.SiteCode, d)
                else:
                    logging.info("Request for data for %s between dates %s and %s failed",
                                 site.SiteCode, date, (date + dbm.days(1)).date())

            else:
                logging.info("Skipping site %s for date: %s as data is already in the DB",
                             dbm.red(site.SiteCode), dbm.red(date_range[i].date()))
                logging.info("To force overwriting provide the -f flag.")

        session.commit()


def main():
    start_date, end_date, force = dbm.process_args()
    db_info = dbm.load_db_info('.aqe_secret.json')

    logging.info("Starting aqe_database script")
    logging.info("Has internet connection: %s", dbm.connected_to_internet())

    # Connect to the database
    connection_string = dbm.create_connection_string(host=db_info["host"],
                                                     port=db_info["port"],
                                                     dbname=db_info["db_name"],
                                                     user=db_info["username"],
                                                     password=db_info["password"])
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # Update the aqe_sites database table
    update_site_list_table(session)

    # Update data in aqe reading table
    update_reading_table(session, start_date=str(start_date), end_date=str(end_date), force=force)
    logging.info("AQE jobs finished")


if __name__ == '__main__':
    main()

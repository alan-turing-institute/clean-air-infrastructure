"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
import requests
from .databases import Updater, laqn_tables
from .loggers import green
from sqlalchemy import func, text
from datetime import datetime
import pandas as pd 
import calendar

class LAQNDatabase(Updater):
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Ensure that tables exist
        laqn_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """
        Request all laqn sites
        Remove any that do not have an opening date
        """
        try:
            endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json"
            raw_data = self.api.get_response(endpoint, timeout=5.0).json()["Sites"]["Site"]
            # Remove sites with no opening date
            processed_data = [site for site in raw_data if site['@DateOpened']]
            if len(processed_data) != len(raw_data):
                self.logger.warning("Excluded %i sites which do not have an opening date from the database",
                                    len(raw_data) - len(processed_data))
            return processed_data
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    def request_site_readings(self, site_code, start_date, end_date):
        """
        Request all readings for {site_code} between {start_date} and {end_date}
        Remove duplicates and add the site_code
        """
        try:
            endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(
                site_code, str(start_date.date()), str(end_date.date())
            )
            raw_data = self.api.get_response(endpoint, timeout=5.0).json()["AirQualityData"]["Data"]
            # Drop duplicates
            processed_data = [dict(t) for t in {tuple(d.items()) for d in raw_data}]
            # Add the site_code
            for reading in processed_data:
                reading["@SiteCode"] = site_code
            return processed_data
        except (requests.exceptions.HTTPError) as e:
            self.logger.warning("Request to %s failed: %s", endpoint, e)
            return None
        except (TypeError, KeyError):
            return None

    def update_site_list_table(self):
        """
        Update the laqn_site table
        """
        self.logger.info("Starting LAQN site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("KCL API"))
            site_entries = [laqn_tables.build_site_entry(site) for site in self.request_site_entries()]
            self.logger.info("Updating site info database records")
            session.add_all(site_entries)
            self.logger.info("Committing changes to database table %s", green(laqn_tables.LAQNSite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """Update the database with new sensor readings."""
        self.logger.info("Starting LAQN readings update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(laqn_tables.LAQNSite)
            self.logger.info("Requesting readings from %s for %s sites",
                             green("KCL API"), green(len(list(site_info_query))))

            # Get all readings for each site between its start and end dates and update the database
            site_readings = self.get_available_readings(site_info_query)
            session.add_all([laqn_tables.build_reading_entry(site_reading) for site_reading in site_readings])

            # Commit changes
            self.logger.info("Committing changes to database table %s", green(laqn_tables.LAQNReading.__tablename__))
            session.commit()

    def __get_sites_within_geom(self, boundary_geom):
        """
        Return all the sites that fall within a geometry object
        """
        with self.dbcnxn.open_session() as session:

            return session.query(laqn_tables.LAQNSite).\
                           filter(laqn_tables.LAQNSite.geom.ST_Intersects(boundary_geom))


    def query_interest_points(self, boundary_geom):
        """
        Return interest points where interest points are
            the locations of laqn sites
        """

        with self.dbcnxn.open_session() as session:

            return session.query(('laqn_' + laqn_tables.LAQNSite.SiteCode).label('id'), 
                                 laqn_tables.LAQNSite.Latitude.label("lat"),
                                 laqn_tables.LAQNSite.Longitude.label("lon"), 
                                 laqn_tables.LAQNSite.geom.label('geom')
                                 ).filter(laqn_tables.LAQNSite.geom.\
                                        ST_Intersects(boundary_geom)) 

    def __query_interest_points(self, boundary_geom):
        """
        Return interest points where interest points are
            the locations of laqn sites
        """

        with self.dbcnxn.open_session() as session:

            return session.query(laqn_tables.LAQNReading, laqn_tables.LAQNSite.Latitude, laqn_tables.LAQNSite.Longitude).\
                                join(laqn_tables.LAQNSite).\
                                filter(laqn_tables.LAQNSite.geom.ST_Intersects(boundary_geom)).\
                                filter(func.date(laqn_tables.LAQNReading.MeasurementDateGMT) <= datetime.strptime(end_date, '%Y-%m-%d')).\
                                filter(func.date(laqn_tables.LAQNReading.MeasurementDateGMT) >= datetime.strptime(start_date, '%Y-%m-%d'))

    def get_interest_points(self, boundary_geom, start_date, end_date):
        """
        Return a pandas dataframe of interest points in time
        (between the start date and end date) and space (lat/lon)
        Interest points are the locations of LAQN sensors within the london boundary at each time that a reading was captured
        """

        interest_point_query = self.__get_interest_points_query(boundary_geom, start_date, end_date)

        # Get query results in pandas dataframe
        df = pd.read_sql(interest_point_query.statement, self.dbcnxn.engine)

        # Add and rename columns
        df['epoch'] = df['MeasurementDateGMT'].apply(lambda x: calendar.timegm(x.timetuple()))
        df['src'] = 'laqn'

        # Get the columns of interest
        df_subset = df[['src', 'SiteCode', 'MeasurementDateGMT', 'epoch', 'Latitude', 'Longitude']].copy()
        
        # Rename columns
        df_subset.rename(columns={'MeasurementDateGMT': 'datetime',
                                  'SiteCode': 'id', 
                                  'Latitude': 'lat',
                                  'Longitude': 'lon'}, inplace=True)

        # Drop duplicate rows
        return df_subset.drop_duplicates().sort_values(['id', 'datetime'])


# column_names = ['src', 'id', 'datetime', 'epoch', 'lat', 'lon']
# column_types = [np.int, np.int, np.str, np.int, np.float64, np.float64]

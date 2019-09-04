"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
import requests
from .databases import Updater, laqn_tables
from .loggers import green
from .apis import APIReader
from sqlalchemy import func, and_
import pandas as pd


class LAQNDatabase(Updater, APIReader):
    def __init__(self, *args, **kwargs):
        # Initialise the base classes
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
            raw_data = self.get_response(endpoint, timeout=5.0).json()["Sites"]["Site"]
            # Remove sites with no opening date
            processed_data = [site for site in raw_data if site['@DateOpened']]
            if len(processed_data) != len(raw_data):
                self.logger.warning("Excluded %i site(s) with no opening date from the database",
                                    len(raw_data) - len(processed_data))
            return processed_data
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    def request_site_readings(self, start_date, end_date, site_code):
        """
        Request all readings for {site_code} between {start_date} and {end_date}
        Remove duplicates and add the site_code
        """
        try:
            endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(
                site_code, str(start_date.date()), str(end_date.date())
            )
            raw_data = self.get_response(endpoint, timeout=5.0).json()["AirQualityData"]["Data"]
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
        self.logger.info("Starting %s readings update...", green("LAQN"))

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(laqn_tables.LAQNSite)
            self.logger.info("Requesting readings from %s for %s sites",
                             green("KCL API"), green(len(list(site_info_query))))

            # Get all readings for each site between its start and end dates and update the database
            site_readings = self.get_readings_by_site(site_info_query, self.start_date, self.end_date)
            session.add_all([laqn_tables.build_reading_entry(site_reading) for site_reading in site_readings])

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(len(site_readings)),
                             green(laqn_tables.LAQNReading.__tablename__))
            session.commit()

        self.logger.info("Finished %s readings update...", green("LAQN"))
        
    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()

    def query_interest_points(self, boundary_geom, include_sites = None):
        """
        Return interest points where interest points are
            the locations of laqn sites within a boundary_geom (e.g. all the sites within London)
        Keyword arguments:
            include_sites -- A list of SiteCodes to include. If None then gets all
    
        """

        with self.dbcnxn.open_session() as session:

            result = session.query(laqn_tables.LAQNSite)
                    
            if not include_sites:
                filtered_result = result.filter(laqn_tables.LAQNSite.geom.ST_Intersects(boundary_geom))
            
            else:
                filtered_result = result.filter(and_(
                                          laqn_tables.LAQNSite.geom.ST_Intersects(boundary_geom),
                                          laqn_tables.LAQNSite.SiteCode.in_(include_sites))
                                         )
        return filtered_result


    def query_interest_point_buffers(self, buffer_sizes, boundary_geom, include_sites = None, num_seg_quarter_circle = 8):
        """
        Return a set of buffers of size buffer_sizes around the interest points 
        returned by self.query_interest_points
        """

        interest_point_query = self.query_interest_points(boundary_geom, include_sites).subquery()

        func_base = lambda x, size: func.Geometry(func.ST_Buffer(func.Geography(x), size, num_seg_quarter_circle))
        
        query_funcs = [func_base(interest_point_query.c.geom, size).label('buffer_' + str(size)) for size in buffer_sizes]

        with self.dbcnxn.open_session() as session:
            out = session.query(interest_point_query.c.SiteCode.label('id'), 
                                    interest_point_query.c.Latitude.label("lat"),
                                    interest_point_query.c.Longitude.label("lon"), 
                                    *query_funcs)

        return out


    def query_interest_point_readings(self, start_date, end_date, boundary_geom, include_sites):
        """
        Get readings from interest points between dates of interest, passing a list of sites to get readings for
        """

        # start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
        # end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

        subquery = self.query_interest_points(boundary_geom, include_sites).subquery()

        with self.dbcnxn.open_session() as session:

            result = session.query(subquery.c.SiteCode.label("id"), 
                                   laqn_tables.LAQNReading.MeasurementDateGMT.label('time'),
                                   laqn_tables.LAQNReading.SpeciesCode,
                                   laqn_tables.LAQNReading.Value
                                   
                                   
                                   ).join(laqn_tables.LAQNReading)
            result = result.filter(laqn_tables.LAQNReading.MeasurementDateGMT.between(start_date, end_date))
            df = pd.read_sql(result.statement, self.dbcnxn.engine)

            df = pd.pivot_table(df, 
                                values = 'Value', 
                                index=['id', 'time'], 
                                columns = 'SpeciesCode', dropna=False).reset_index()
            return df
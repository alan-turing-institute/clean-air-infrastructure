"""
Satellite
"""
import datetime
import requests
from ..mixins import APIRequestMixin, DateRangeMixin
from ..databases import DBWriter
from ..databases.tables import MetaPoint, LAQNSite, LAQNReading
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime


class SatelliteWriter(APIRequestMixin, DBWriter):
    """
    Get Satellite data from 
    (https://download.regional.atmosphere.copernicus.eu/services/CAMS50)
    """
    def __init__(self, copernicus_key, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
        
        self.access_key = copernicus_key

    def request_satellite_data(self, start_date, pollutant, data_type):
        """
        Request satellite data

        args:
            start_date: Date to collect data from           
            pollutant: 'NO2', 'NO', 'PM10'
            type: Either 'archieve' or 'forecast
        """

        if data_type == 'archive':
            call_type = 'ANALYSIS'
            time_required = '-24H-1H'
        elif data_type=='forecast':
            call_type = 'FORECAST_'
            time_required = '0H24H'

        level = 'SURFACE'
        referencetime = start_date + 'T00:00:00Z'

        params = {'token': self.access_key,
                  'grid': '0.1',
                  'model': 'ENSEMBLE',
                  'package': "_".join([call_type, pollutant, level]),
                  'time': time_required,
                  'referencetime': referencetime,
                  'format': 'GRIB2'
                 } 

        try:
            endpoint = "https://download.regional.atmosphere.copernicus.eu/services/CAMS50"
            
            raw_data = self.get_response(endpoint, timeout=30.)
            print(raw_data)

            # # Remove sites with no opening date
            # processed_data = [site for site in raw_data if site['@DateOpened']]
            # if len(processed_data) != len(raw_data):
            #     self.logger.warning("Excluded %i site(s) with no opening date from the database",
            #                         len(raw_data) - len(processed_data))
            # return processed_data
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    # def request_site_readings(self, start_date, end_date, site_code):
    #     """
    #     Request all readings for {site_code} between {start_date} and {end_date}
    #     Remove duplicates and add the site_code
    #     """
    #     try:
    #         endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(
    #             site_code, str(start_date), str(end_date)
    #         )
    #         raw_data = self.get_response(endpoint, timeout=120.0).json()["AirQualityData"]["Data"]
    #         # Drop duplicates
    #         processed_data = [dict(t) for t in {tuple(d.items()) for d in raw_data}]
    #         # Add the site_code
    #         for reading in processed_data:
    #             reading["SiteCode"] = site_code
    #             timestamp_start = datetime_from_str(reading.pop("@MeasurementDateGMT"), timezone="GMT", rounded=True)
    #             timestamp_end = timestamp_start + datetime.timedelta(hours=1)
    #             reading["MeasurementStartUTC"] = utcstr_from_datetime(timestamp_start)
    #             reading["MeasurementEndUTC"] = utcstr_from_datetime(timestamp_end)
    #         return processed_data
    #     except requests.exceptions.HTTPError as error:
    #         self.logger.warning("Request to %s failed:", endpoint)
    #         self.logger.warning(error)
    #         return None
    #     except (TypeError, KeyError):
    #         return None

    # def update_site_list_table(self):
    #     """
    #     Update the laqn_site table
    #     """
    #     self.logger.info("Starting LAQN site list update...")

    #     # Open a DB session
    #     with self.dbcnxn.open_session() as session:
    #         # Reload site information and update the database accordingly
    #         self.logger.info("Requesting site info from %s", green("KCL API"))

    #         # Retrieve site entries (discarding any that do not have a known position)
    #         site_entries = [s for s in self.request_site_entries() if s["@Latitude"] and s["@Longitude"]]
    #         for entry in site_entries:
    #             entry["geometry"] = MetaPoint.build_ewkt(entry["@Latitude"], entry["@Longitude"])

    #         # Only consider unique sites
    #         unique_sites = {s["geometry"]: MetaPoint.build_entry("laqn", geometry=s["geometry"])
    #                         for s in site_entries}

    #         # Update the interest_points table and retrieve point IDs
    #         point_id = {}
    #         for geometry, interest_point in unique_sites.items():
    #             merged_point = session.merge(interest_point)
    #             session.flush()
    #             point_id[geometry] = str(merged_point.id)

    #         # Add point IDs to the site_entries
    #         for entry in site_entries:
    #             entry["point_id"] = point_id[entry["geometry"]]

    #         # Build the site entries and commit
    #         self.logger.info("Updating site info database records")
    #         for site in site_entries:
    #             session.merge(LAQNSite.build_entry(site))
    #         self.logger.info("Committing changes to database tables %s and %s",
    #                          green(MetaPoint.__tablename__),
    #                          green(LAQNSite.__tablename__))
    #         session.commit()

    # def update_reading_table(self, usecore=True):
    #     """Update the readings table with new sensor readings."""
    #     self.logger.info("Starting %s readings update...", green("LAQN"))

    #     # Open a DB session
    #     with self.dbcnxn.open_session() as session:
    #         # Load readings for all sites and update the database accordingly
    #         site_info_query = session.query(LAQNSite)
    #         self.logger.info("Requesting readings from %s for %s sites",
    #                          green("KCL API"), green(len(list(site_info_query))))

    #     # Get all readings for each site between its start and end dates and update the database
    #     site_readings = self.get_readings_by_site(site_info_query, self.start_date, self.end_date)
    #     site_records = [LAQNReading.build_entry(site_reading, return_dict=usecore)
    #                     for site_reading in site_readings]

    #     # Open a DB session
    #     with self.dbcnxn.open_session() as session:
    #         # Commit the records to the database
    #         if usecore:
    #             self.add_records(session, site_records, flush=True, table=LAQNReading)
    #         else:
    #             self.add_records(session, site_records, flush=True)

    #         # Commit changes
    #         self.logger.info("Committing %s records to database table %s",
    #                          green(len(site_readings)),
    #                          green(LAQNReading.__tablename__))
    #         session.commit()

    #     self.logger.info("Finished %s readings update", green("LAQN"))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.request_satellite_data('2019-11-01', "NO2", 'forecast')

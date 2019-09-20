"""
LAQN
"""
import datetime
from geoalchemy2.functions import ST_AsEWKT
import requests
from sqlalchemy.exc import IntegrityError
from ..apis import APIReader
from ..databases import Writer, laqn_tables, interest_point_table
from ..loggers import green
from ..timestamps import datetime_from_str, utcstr_from_datetime


class LAQNWriter(Writer, APIReader):
    """
    Get data from the LAQN network via the API maintained by Kings College London:
    (https://www.londonair.org.uk/Londonair/API/)
    """
    def request_site_entries(self):
        """
        Request all LAQN sites
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
                site_code, str(start_date), str(end_date)
            )
            raw_data = self.get_response(endpoint, timeout=5.0).json()["AirQualityData"]["Data"]
            # Drop duplicates
            processed_data = [dict(t) for t in {tuple(d.items()) for d in raw_data}]
            # Add the site_code
            for reading in processed_data:
                reading["SiteCode"] = site_code
                timestamp_start = datetime_from_str(reading.pop("@MeasurementDateGMT"), timezone="GMT", rounded=True)
                timestamp_end = timestamp_start + datetime.timedelta(hours=1)
                reading["MeasurementStartUTC"] = utcstr_from_datetime(timestamp_start)
                reading["MeasurementEndUTC"] = utcstr_from_datetime(timestamp_end)
            return processed_data
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed:", endpoint)
            self.logger.warning(error)
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

            # Retrieve site entries (discarding any that do not have a known position)
            site_entries = [s for s in self.request_site_entries() if s["@Latitude"] and s["@Longitude"]]
            for entry in site_entries:
                entry["geometry"] = interest_point_table.EWKT_from_lat_long(entry["@Latitude"], entry["@Longitude"])

            # Add all distinct points to the interest_points table
            session.add_all([interest_point_table.build_entry("laqn", geometry=geom)
                            for geom in {s["geometry"] for s in site_entries}])

            # Get point IDs for each of these points
            point_id = {_geom: _id for _id, _geom in session.query(
                interest_point_table.InterestPoint.point_id, ST_AsEWKT(interest_point_table.InterestPoint.location)
            ).filter(interest_point_table.InterestPoint.source == "laqn")}

            # Add point IDs to the site_entries
            for entry in site_entries:
                entry["point_id"] = str(point_id[entry["geometry"]])

            # Build the site entries and commit
            self.logger.info("Updating site info database records")
            session.add_all([laqn_tables.build_site_entry(site) for site in site_entries])
            self.logger.info("Committing changes to database tables %s and %s",
                             green(interest_point_table.InterestPoint.__tablename__),
                             green(laqn_tables.LAQNSite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """Update the readings table with new sensor readings."""
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
            try:
                session.commit()
            except IntegrityError:
                self.logger.warning("Records were not committed as one or more of them were duplicates")

        self.logger.info("Finished %s readings update", green("LAQN"))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()

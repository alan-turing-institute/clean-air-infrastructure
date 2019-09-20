"""
Get data from the AQE network via the API
"""
import csv
import datetime
import io
from xml.dom import minidom
import requests
from ..apis import APIReader
from ..databases import Writer, aqe_tables, interest_point_table
from ..loggers import green
from ..timestamps import datetime_from_str, utcstr_from_datetime


class AQEWriter(Writer, APIReader):
    """Manage interactions with the AQE table on Azure"""
    def request_site_entries(self):
        """
        Request all AQE sites
        Remove any that do not have an opening date
        """
        try:
            endpoint = "http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site"
            raw_data = self.get_response(endpoint, timeout=5.0).content
            dom = minidom.parse(io.BytesIO(raw_data))
            # Convert DOM object to a list of dictionaries. Each dictionary is an site containing site information
            return [dict(s.attributes.items()) for s in dom.getElementsByTagName("Site")]
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
            endpoint = "http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/{}/{}/{}".format(
                site_code, str(start_date), str(end_date)
            )
            raw_data = self.get_response(endpoint, timeout=5.0).content
            # Process CSV data
            csvreader = csv.reader(io.StringIO(raw_data.decode()))
            # Extract species names from the column headers
            header = csvreader.__next__()
            species = [s.split(": ")[1].split(" ")[0] for s in header[1:]]
            # Process the readings which are in the format: Date, Species1, Species2, ...
            processed_readings = []
            for reading in csvreader:
                timestamp_end = datetime_from_str(reading[0], timezone="GMT", rounded=True)
                timestamp_start = timestamp_end - datetime.timedelta(hours=1)
                for species_code, value in zip(species, reading[1:]):
                    processed_readings.append({"SiteCode": site_code,
                                               "SpeciesCode": species_code,
                                               "MeasurementStartUTC": utcstr_from_datetime(timestamp_start),
                                               "MeasurementEndUTC": utcstr_from_datetime(timestamp_end),
                                               "Value": value})
            return processed_readings
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed:", endpoint)
            self.logger.warning(error)
            return None
        except (TypeError, KeyError):
            return None

    def update_site_list_table(self):
        """Update the aqe_site table"""
        self.logger.info("Starting AQE site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("aeat.com API"))

            # Retrieve site entries (discarding any that do not have a known position)
            site_entries = [s for s in self.request_site_entries() if s["Latitude"] and s["Longitude"]]

            # Add all points to the interest_points table
            points = [interest_point_table.build_entry("aqe", latitude=s["Latitude"], longitude=s["Longitude"])
                      for s in site_entries]
            session.add_all(points)

            # Flush the session and refresh in order to obtain the IDs of these points
            session.flush()
            for point in points:
                session.refresh(point)

            # Add point IDs to each of the site entries
            for site, point in zip(site_entries, points):
                site["point_id"] = point.point_id

            # Build the site entries and commit
            self.logger.info("Updating site info database records")
            session.add_all([aqe_tables.build_site_entry(site) for site in site_entries])
            self.logger.info("Committing changes to database tables %s and %s",
                             green(interest_point_table.InterestPoint.__tablename__),
                             green(aqe_tables.AQESite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """Update the readings table with new sensor readings."""
        self.logger.info("Starting %s readings update...", green("AQE"))

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(aqe_tables.AQESite)
            self.logger.info("Requesting readings from %s for %s sites",
                             green("aeat.com API"), green(len(list(site_info_query))))

            # Get all readings for each site between its start and end dates and update the database
            site_readings = self.get_readings_by_site(site_info_query, self.start_date, self.end_date)
            # session.add_all([aqe_tables.build_reading_entry(site_reading) for site_reading in site_readings])
            readings = [aqe_tables.build_reading_entry(site_reading) for site_reading in site_readings]
            print(readings)
            session.add_all(readings)

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(len(site_readings)),
                             green(aqe_tables.AQEReading.__tablename__))
            session.commit()
        self.logger.info("Finished %s readings update", green("AQE"))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()

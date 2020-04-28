"""
Get data from the AQE network via the API
"""
import csv
import datetime
import io
from xml.dom import minidom
import pandas
import requests
from ..mixins import DateRangeMixin, APIRequestMixin
from ..databases import DBWriter
from ..databases.tables import AQESite, AQEReading, MetaPoint
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime


class AQEWriter(DateRangeMixin, APIRequestMixin, DBWriter):
    """Manage interactions with the AQE table on Azure"""

    # Set list of primary-key columns
    reading_keys = [
        "SiteCode",
        "SpeciesCode",
        "MeasurementStartUTC",
        "MeasurementEndUTC",
    ]

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def request_site_entries(self):
        """
        Request all AQE sites
        Remove any that do not have an opening date
        """
        try:
            endpoint = (
                "http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site"
            )
            raw_data = self.get_response(endpoint, timeout=5.0).content
            dom = minidom.parse(io.BytesIO(raw_data))
            # Convert DOM object to a list of dictionaries. Each dictionary is an site containing site information
            return [
                dict(s.attributes.items()) for s in dom.getElementsByTagName("Site")
            ]
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
            raw_data = self.get_response(endpoint, timeout=120.0).content
            # Process CSV data
            csvreader = csv.reader(io.StringIO(raw_data.decode()))
            # Extract species names from the column headers
            header = csvreader.__next__()
            species = [s.split(": ")[1].split(" ")[0] for s in header[1:]]
            # Process the readings which are in the format: Date, Species1, Species2, ...
            readings = []
            for reading in csvreader:
                timestamp_end = datetime_from_str(
                    reading[0], timezone="GMT", rounded=True
                )
                timestamp_start = timestamp_end - datetime.timedelta(hours=1)
                for species_code, value in zip(species, reading[1:]):
                    # Ignore empty values
                    try:
                        value = float(value)
                    except ValueError:
                        self.logger.debug(
                            "Could not interpret '%s' as a measurement", value
                        )
                        continue
                    # Construct a new reading
                    readings.append(
                        {
                            "SiteCode": site_code,
                            "SpeciesCode": species_code,
                            "MeasurementStartUTC": utcstr_from_datetime(
                                timestamp_start
                            ),
                            "MeasurementEndUTC": utcstr_from_datetime(timestamp_end),
                            "Value": float(value),
                        }
                    )
            # Combine any readings taken within the same hour
            df_readings = pandas.DataFrame(readings)
            df_combined = df_readings.groupby(self.reading_keys, as_index=False).agg(
                {"Value": "mean"}
            )
            return list(df_combined.T.to_dict().values())
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
            site_entries = [
                s
                for s in self.request_site_entries()
                if s["Latitude"] and s["Longitude"]
            ]
            for entry in site_entries:
                entry["geometry"] = MetaPoint.build_ewkt(
                    entry["Latitude"], entry["Longitude"]
                )

            # Only consider unique sites
            unique_sites = {
                s["geometry"]: MetaPoint.build_entry("aqe", geometry=s["geometry"])
                for s in site_entries
            }

            # Update the interest_points table and retrieve point IDs
            point_id = {}
            for geometry, interest_point in unique_sites.items():
                merged_point = session.merge(interest_point)
                session.flush()
                point_id[geometry] = str(merged_point.id)

            # Add point IDs to the site_entries
            for entry in site_entries:
                entry["point_id"] = point_id[entry["geometry"]]

            # Update the sites table and commit any changes
            self.logger.info("Updating site info database records")
            for site in site_entries:
                session.merge(AQESite.build_entry(site))
            self.logger.info(
                "Committing changes to database tables %s and %s",
                green(MetaPoint.__tablename__),
                green(AQESite.__tablename__),
            )
            session.commit()

    def update_reading_table(self, usecore=True):
        """Update the readings table with new sensor readings."""
        self.logger.info(
            "Starting %s readings update using data from %s to %s...",
            green("AQE"),
            self.start_datetime,
            self.end_datetime,
        )

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(AQESite)
            self.logger.info(
                "Requesting readings from %s for %s sites",
                green("aeat.com API"),
                green(len(list(site_info_query))),
            )

        # Get all readings for each site between its start and end dates and update the database
        site_readings = self.get_readings_by_site(
            site_info_query, self.start_date, self.end_date
        )
        site_records = [
            AQEReading.build_entry(site_reading, return_dict=usecore)
            for site_reading in site_readings
        ]

        # Commit the records to the database
        self.commit_records(site_records, on_conflict="ignore", table=AQEReading)

        # Commit changes
        self.logger.info(
            "Committing %s records to database table %s",
            green(len(site_readings)),
            green(AQEReading.__tablename__),
        )

        self.logger.info("Finished %s readings update", green("AQE"))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()

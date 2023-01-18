
from datetime import datetime, timedelta
import pytz
import requests
import json
from ..mixins.api_request_mixin import APIRequestMixin
from ..mixins.date_range_mixin import DateRangeMixin
from ..mixins.availability_mixins import LAQNAvailabilityMixin
from ..mixins.availability_mixins.breathe_availability import BreatheAvailabilityMixin
from ..databases import DBWriter
from ..databases.tables import MetaPoint, LAQNSite, LAQNReading
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime

class BreatheWriter(DateRangeMixin, APIRequestMixin, BreatheAvailabilityMixin, DBWriter):
    """
    Get data from the Breathe London network via the API maintained by Imperial College London:
    (https://www.breathelondon.org/developers)
    """

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
    def request_site_entries(self):
        """
        Request all Breathe sites
        """
        try:
            endpoint = (
                "https://api.breathelondon.org/api/ListSensors?key=fe47645a-e87a-11eb-9a03-0242ac130003"
            )
            
            breathe_data = self.get_response(endpoint, timeout=5.0).content # request all the data
            breathe = json.load(breathe_data.decode())
            raw_data = breathe[0]
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            raw_data = {}
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None
    def request_site_readings(self, start_date, end_date, site_code, species, averaging):
        """
        Request all readings for {site_code}, {species} between {start_date} and {end_date} {averaging} eg:hourly
        Remove duplicates and add the site_code
        """
        try:
            # This call retrieves data from Breathe London nodes as a JSON object.
            endpoint = "http://api.breathelondon.org/api/api/getClarityData/{}/{}/{}/{}/{}".format(
                site_code, species, str(start_date), str(end_date), averaging
            )
            sites = self.get_response(endpoint, timeout=120.0).content
            raw_data =sites.decode()
            parsed_data = json.loads(raw_data)
            # Add the site_code
            for reading in parsed_data:
                reading["SiteCode"] = site_code
                # Use strptime to convert the string to a datetime object
                start_time = reading["DateTime"]
                date_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                utc_time = pytz.utc.localize(date_time_obj)
                # convert to UTC
                formatted_date_time = utc_time.strftime("%Y-%m-%d %H:%M:%S")
                timestamp_start = datetime_from_str(
                    str(formatted_date_time), timezone="GMT", rounded=True
                )
                timestamp_end = timestamp_start + timedelta(hours=1)
                reading["MeasurementStartUTC"] = utcstr_from_datetime(timestamp_start)
                reading["MeasurementEndUTC"] = utcstr_from_datetime(timestamp_end)
            return parsed_data
        
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed:", endpoint)
            self.logger.warning(error)
            return None
        except (TypeError, KeyError):
            return None
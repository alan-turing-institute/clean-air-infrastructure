import datetime
import requests
from ..mixins.api_request_mixin import APIRequestMixin, DateRangeMixin
from ..mixins.availability_mixins import LAQNAvailabilityMixin
from ..databases import DBWriter
from ..databases.tables import MetaPoint, LAQNSite, LAQNReading
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime

class BreatheWrite():
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
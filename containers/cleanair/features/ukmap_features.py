"""
UKMAP feature extraction
"""
from .features import Features
from .feature_funcs import sum_area, max_
from ..databases.tables import UKMap


class UKMapFeatures(Features):
    """Extract features for UKMap"""

    @property
    def table(self):
        return UKMap

    @property
    def features(self):
        return {
            "hospitals": {"type": "geom", "feature_dict": {"landuse": ["Hospitals"]}, 'aggfunc': sum_area},
            "museums": {"type": "geom", "feature_dict": {"landuse": ["Museum"]}, 'aggfunc': sum_area},
            "park": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"],
                                                      "landuse": ["Recreational open space"]}, 'aggfunc': sum_area},
            "water": {"type": "geom", "feature_dict": {"feature_type": ["Water"]}, 'aggfunc': sum_area},
             "building_height": {"type": "value", "feature_dict": {"calculated_height_of_building": ["*"]},
                                "aggfunc": max_},
            "flat": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated", "Water"]}, 'aggfunc': sum_area},
            "grass": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"]}, 'aggfunc': sum_area},
        }

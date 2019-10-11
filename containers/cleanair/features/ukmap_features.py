"""
UKMAP feature extraction
"""
from sqlalchemy import func, or_
from .static_features import StaticFeatures
from ..databases.tables import UKMap


class UKMapFeatures(StaticFeatures):
    """Extract features for UKMap"""
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])
        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.features = {
            "building_height": {"type": "value", 'feature_dict': {"feature_type": ["Building"]}},
            "flat": {"type": "geom", 'feature_dict': {"feature_type": ["Vegetated", "Water"]}},
            "grass": {"type": "geom", 'feature_dict': {"feature_type": ["Vegetated"]}},
            "hospitals": {"type": "geom", 'feature_dict': {"landuse": ["Hospitals"]}},
            "museums": {"type": "geom", 'feature_dict': {"landuse": ["Museum"]}},
            "park": {"type": "geom", 'feature_dict': {"feature_type": ["Vegetated"],
                                                      "landuse": ["Recreational open space"]}},
            "water": {"type": "geom", 'feature_dict': {"feature_type": ["Water"]}},
        }

    def query_features(self, feature_name):
        """Query UKMap, selecting all features matching the requirements in the feature_dict"""
        with self.dbcnxn.open_session() as session:
            columns = [UKMap.geom, func.Geography(UKMap.geom).label("geom_geog"), UKMap.feature_type]
            if feature_name == "building_height":
                columns.append(UKMap.calculated_height_of_building)
            else:
                columns.append(UKMap.landuse)
            q_source = session.query(*columns)
            for column, values in self.ukmap_features[feature_type].items():
                q_source = q_source.filter(or_(*[getattr(UKMap, column) == value for value in values]))
        return q_source

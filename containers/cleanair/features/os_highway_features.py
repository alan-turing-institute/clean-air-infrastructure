"""
OS Highway feature extraction
"""
from sqlalchemy import or_
from .static_features import StaticFeatures
from .feature_funcs import sum_length
from ..databases.tables import OSHighway


class OSHighwayFeatures(StaticFeatures):
    """Extract features for OSHighways"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.features = {
            "total_road_length": {"type": "geom",
                                  "feature_dict": {},
                                  "aggfunc": sum_length},
            "total_a_road_prim_length":  {"type": "geom",
                                          "feature_dict": {"route_hierarchy": ["A Road Primary"]},
                                          "aggfunc": sum_length},
            "total_a_road_length": {"type": "geom",
                                    "feature_dict": {"route_hierarchy": ["A Road"]},
                                    "aggfunc": sum_length},
            "total_b_road_length": {"type": "geom",
                                    "feature_dict": {"route_hierarchy": ["B Road", "B Road Primary"]},
                                    "aggfunc": sum_length},
            "total_length": {"type": "geom",
                             "feature_dict":  {"route_hierarchy": ["*"]},
                             "aggfunc": sum_length},
        }

    def query_features(self, feature_name):
        """Query OS highways, selecting all features matching the requirements in feature_dict"""
        with self.dbcnxn.open_session() as session:
            columns = [OSHighway.geom, OSHighway.route_hierarchy]
            q_source = session.query(*columns)
            for column, values in self.features[feature_name]["feature_dict"].items():
                q_source = q_source.filter(or_(*[getattr(OSHighway, column) == value for value in values]))
        return q_source

    def query_feature_values(self, feature_name, q_metapoints, q_geometries):
        pass

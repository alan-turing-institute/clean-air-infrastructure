"""
OS Highway feature extraction
"""
from sqlalchemy import func, or_, between, cast, Integer
from .static_features import StaticFeatures
from ..databases.tables import OSHighway

class OSHFeatures(StaticFeatures):

    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])
        # Initialise parent classes
        super().__init__(**kwargs)

         # List of features to extract
        self.features = {
            "total_road_length": {"type": "geom", 'feature_dict': {"route_hierarchy": ["*"]}},
            "total_a_road_prim_length":  {"type": "geom", 'feature_dict': {"route_hierarchy": ["A Road Primary"]}},
            "total_a_road_length": {"type": "geom", 'feature_dict': {"route_hierarchy": ["A Road"]}},
            "total_b_road_length": {"type": "geom", 'feature_dict': {"route_hierarchy": ["B Road", "B Road Primary"]}},
            "total_length": {"type": "geom", 'feature_dict':  {"route_hierarchy": ["*"]}},
        }

    def query_features(self, feature_name, feature_dict):
        """Query UKMap, selecting all features matching the requirements in feature_dict"""
        with self.dbcnxn.open_session() as session:
            q_source = session.query(OSHighway.geom, OSHighway.route_hierarchy)
            for column, values in feature_dict.items():
                if not values[0] == '*':
                    q_source = q_source.filter(or_(*[getattr(OSHighway, column) == value for value in values]))
        return q_source

        


        

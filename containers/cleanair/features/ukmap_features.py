"""
UKMAP feature extraction
"""
from sqlalchemy import between, cast, func, Integer, literal, or_
from .static_features import StaticFeatures
from .feature_funcs import sum_area
from ..databases.tables import UKMap


class UKMapFeatures(StaticFeatures):
    """Extract features for UKMap"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.features = {           
            # "museums": {"type": "geom", "feature_dict": {"landuse": ["Museum"]}, 'aggfunc': sum_area},
            "flat": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated", "Water"]}, 'aggfunc': sum_area},
            # "building_height": {"type": "value", "feature_dict": {"feature_type": ["Building"]}},
            # "grass": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"]}, 'aggfunc': sum_area},
            # "hospitals": {"type": "geom", "feature_dict": {"landuse": ["Hospitals"]}, 'aggfunc': sum_area},
            # "park": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"],
            #                                           "landuse": ["Recreational open space"]}, 'aggfunc': sum_area},
            # "water": {"type": "geom", "feature_dict": {"feature_type": ["Water"]}, 'aggfunc': sum_area},
        }

    def query_features(self, feature_name):
        """Query UKMap, selecting all features matching the requirements in the feature_dict"""
        with self.dbcnxn.open_session() as session:
            # Construct column selector
            columns = [UKMap.geom, UKMap.feature_type]
            if feature_name == "building_height":
                columns.append(UKMap.calculated_height_of_building)
            else:
                columns.append(UKMap.landuse)
            q_source = session.query(*columns)
            # Construct filters
            filter_list = []
            if feature_name == "building_height":  # filter out unreasonably tall buildings
                filter_list.append(UKMap.calculated_height_of_building < 999.9)
            for column, values in self.features[feature_name]["feature_dict"].items():
                filter_list.append(or_(*[getattr(UKMap, column) == value for value in values]))
            q_source = q_source.filter(*filter_list)
        return q_source

    def query_feature_values(self, feature_name, q_metapoints, q_geometries):
        """Construct one record for each interest point containing the point ID and one value column per buffer"""
        with self.dbcnxn.open_session() as session:
            # Cross join interest point and geometry queries...
            sq_metapoints = q_metapoints.subquery()
            sq_geometries = q_geometries.subquery()

            # ... restrict to only those within max(radius) of one another
            # ... construct a column for each radius, containing building height if the building is inside that radius
            # => [M < Npoints * Ngeometries records]
            sq_within = session.query(sq_metapoints,
                                      sq_geometries,
                                      func.ST_Distance(sq_metapoints.c.location_geog,
                                                       sq_geometries.c.geom_geog).label("distance")
                                      ).filter(func.ST_DWithin(sq_metapoints.c.location_geog,
                                                               sq_geometries.c.geom_geog,
                                                               max(self.buffer_radii_metres))).subquery()

            # Now group these by interest point, aggregating the height columns using the maximum in each group
            # => [Npoints records]
            q_intersections = session.query(sq_within.c.id,
                                            literal(feature_name).label("feature_name"),
                                            *[func.max(
                                                sq_within.c.calculated_height_of_building *
                                                cast(between(getattr(sq_within.c, "distance"), 0, radius), Integer)
                                                ).label(str(radius))
                                              for radius in self.buffer_radii_metres]
                                            ).group_by(sq_within.c.id)

        # Return the overall query
        return q_intersections

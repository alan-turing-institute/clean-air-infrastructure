from .databases import Updater, StaticTableConnector
from sqlalchemy import func, and_, or_, cast, Float

class UKMap(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('ukmap')

    @property
    def convex_hull(self):
        """
        Return the convex hull of the London Boundary as a query object
        """

        with self.open_session() as session:
            return session.scalar(func.ST_ConvexHull(func.ST_Collect(self.table.wkb_geometry)))

    def query_buffer_intersection(self, buffer_query, buffer_col):

        buffer_query = buffer_query.subquery()

        with self.open_session() as session:

            return session.query(
                                buffer_query.c.id,
                                buffer_query.c.lat,
                                buffer_query.c.lon,
                                self.table.feature_type, 
                                self.table.landuse,
                                self.table.calcaulated_height_of_building,
                                func.ST_Intersection(func.ST_MakeValid(self.table.shape), 
                                                     buffer_query.c[buffer_col]).label("intersection") 
                                ).\
                            filter(and_(
                                func.ST_GeometryType(func.ST_MakeValid(self.table.shape))=='ST_MultiPolygon', 
                                func.ST_Intersects(self.table.shape, buffer_query.c[buffer_col])
                                ))

    def __compose_function(self, f1, f2):

        return lambda x: func.coalesce(f1(f2(x)), 0.0)

    def __query_features(self, buffer_intersection_subquery, feature_func, func_label):

        with self.open_session() as session:

            return session.query(
                            buffer_intersection_subquery.c.id,
                            buffer_intersection_subquery.c.lat,
                            buffer_intersection_subquery.c.lon,
                            feature_func[0].label(func_label)
                            ).\
                        filter(feature_func[1]).\
                                group_by(buffer_intersection_subquery.c.id, 
                                         buffer_intersection_subquery.c.lat,
                                         buffer_intersection_subquery.c.lon)

    def query_features(self, buffer_intersection_query):

        buffer_intersection_query = buffer_intersection_query.subquery()

        # Compose functions 
        sum_area = lambda x: func.sum(func.ST_Area(x))
        max_cast = lambda x: func.max(cast(x, Float))

        # Shorthand for geom
        geom = buffer_intersection_query.c.intersection
        
        # Define all the functions as dictionary of 2D lists (function, query)
        feature_functions = {
            'total_museum_area': [sum_area(geom), buffer_intersection_query.c.feature_type=='Museum'],
            'total_hospital_area': [sum_area(geom), buffer_intersection_query.c.landuse=='Hospitals'],
            'total_grass_area': [sum_area(geom), buffer_intersection_query.c.feature_type=='Vegetated'],
            'total_park_area': [sum_area(geom), and_(buffer_intersection_query.c.feature_type=='Vegetated', 
                                               buffer_intersection_query.c.landuse== 'Recreational open space')],
            'total_water_area': [sum_area(geom), buffer_intersection_query.c.feature_type=='Water'],
            'total_flat_area': [sum_area(geom), or_(buffer_intersection_query.c.feature_type=='Vegetated', 
                                               buffer_intersection_query.c.feature_type == 'Water')],
            'max_building_height': [max_cast(buffer_intersection_query.c.calcaulated_height_of_building), None]
        }

        # Iterate over functions
        for key, value in feature_functions.items():

            yield self.__query_features(buffer_intersection_query, value, key)


        # return feature_functions
        # generated_columns = [
        #     ['total_museum_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Museum')"],
        #     ['total_hospital_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Hospitals')"],
        #     ['total_grass_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Vegetated')"],
        #     ['total_park_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Park' or buffer.landuse='Recreational open space')"],
        #     ['total_water_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Water')"],
        #     ['total_flat_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Vegetated' or buffer.feature_type='Water')"],
        #     ['max_building_height', "max(cast(buffer.calcaulated_height_of_building as float))"],
        # ]
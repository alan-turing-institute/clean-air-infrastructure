from .databases import Updater, StaticTableConnector
from sqlalchemy import func, and_, or_, cast, Float

class UKMap(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('ukmap')

    def __query_buffer_intersection(self, buffer_query, buffer_col):
        """
        Gets the intersection between buffers and the ukmap geoms
        """

        buffer_query = buffer_query.subquery()

        with self.open_session() as session:
            out =  session.query(
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
                                
            return out


    def query_features(self, buffer_query, buffer_col):


        # Get buffer intersections
        buffer_intersection_query = self.__query_buffer_intersection(buffer_query, buffer_col).subquery()
        
        # Compose functions 
        sum_area = lambda x, filt: func.sum(func.ST_Area(func.Geography(x))).filter(filt)
        
        max_cast = lambda x: func.max(cast(x, Float))

        # Shorthand for geom
        geom = buffer_intersection_query.c.intersection

        with self.open_session() as session:
            out = session.query(
                            buffer_intersection_query.c.id,
                            func.coalesce(sum_area(geom, buffer_intersection_query.c.feature_type=='Museum'), 0.0).label('total_museum_area'),
                            func.coalesce(sum_area(geom, buffer_intersection_query.c.landuse=='Hospitals'), 0.0).label('total_hospital_area'),
                            func.coalesce(sum_area(geom, buffer_intersection_query.c.feature_type=='Vegetated'), 0.0).label('total_grass_area'),

                            func.coalesce(sum_area(geom, and_(buffer_intersection_query.c.feature_type=='Vegetated', 
                                                              buffer_intersection_query.c.landuse== 'Recreational open space')), 0.0).label('total_park_area'),
                            func.coalesce(sum_area(geom, buffer_intersection_query.c.feature_type=='Water'), 0.0).label('total_water_area '),
                            func.coalesce(sum_area(geom, or_(buffer_intersection_query.c.feature_type=='Vegetated', 
                                                             buffer_intersection_query.c.feature_type == 'Water')), 0.0).label('total_flat_area'),
                            max_cast(buffer_intersection_query.c.calcaulated_height_of_building).label('max_building_height')
                            
                            ).\
                                group_by(buffer_intersection_query.c.id, 
                                         buffer_intersection_query.c.lat,
                                         buffer_intersection_query.c.lon)

            return out
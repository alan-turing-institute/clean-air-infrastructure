from .databases import StaticTableConnector
from sqlalchemy import func, and_, or_, cast, Float
import pandas as pd
from dateutil import rrule
from datetime import datetime


class UKMap(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('ukmap')

    def __query_buffer_intersection(self, buffer_query, buffer_cols):
        """
        Gets the intersection between buffers and the ukmap geoms
        """

        buffer_query = buffer_query.subquery()

        query_items = [buffer_query.c.id,
                       buffer_query.c.lat,
                       buffer_query.c.lon,
                       self.table.feature_type,
                       self.table.landuse,
                       self.table.calculated_height_of_building]

        # Get the intersection between the ukmap geometries and the largest buffer
        largest_intersection = func.ST_Intersection(func.ST_MakeValid(self.table.shape),
                                                    buffer_query.c['buffer_' + buffer_cols[0]]).\
            label("intersect_" + buffer_cols[0])

        query_items = query_items + [largest_intersection]

        # If there are other buffers get the intersection between each buffer and the last intersection geomtry
        if len(buffer_cols) > 1:
            for buff in buffer_cols[1:]:
                next_intersection = func.ST_Intersection(func.ST_MakeValid(query_items[-1]),
                                                         buffer_query.c['buffer_' + buff]).\
                                                         label("intersect_" + buff)
                query_items.append(next_intersection)

        # Create the query and apply filters
        with self.open_session() as session:
            out = session.query(*query_items).\
                            filter(and_(
                                func.ST_GeometryType(func.ST_MakeValid(self.table.shape)) == 'ST_MultiPolygon',
                                func.ST_Intersects(self.table.shape, buffer_query.c['buffer_' + buffer_cols[0]])
                                ))
            return out

    def query_features(self, buffer_query, buffer_sizes, return_df=True):

        if not isinstance(buffer_sizes, list):
            raise TypeError("buffer_sizes object must be a list")

        def __intersected_col_name(size):
            return 'intersect_' + str(size)

        def __summary_f_list(subquery, buffer_size):
            """
            For a given intersected geometry, create summary functions and tag with appropriate label
            """
            geom = subquery.c[__intersected_col_name(buffer_size)]
            return [
                    sum_area(geom, subquery.c.feature_type == 'Museum', s + '_total_museum_area'),
                    sum_area(geom, subquery.c.landuse == 'Hospitals', s + '_total_hospital_area'),
                    sum_area(geom, subquery.c.feature_type == 'Vegetated', s + '_total_grass_area'),
                    sum_area(geom, and_(subquery.c.feature_type == 'Vegetated',
                                        subquery.c.landuse == 'Recreational open space'), s + '_total_park_area'),
                    sum_area(geom, subquery.c.feature_type == 'Water', s + '_total_water_area'),
                    sum_area(geom, or_(subquery.c.feature_type == 'Vegetated',
                                       subquery.c.feature_type == 'Water'), s + '_total_flat_area'),
                    max_cast(subquery.c.calculated_height_of_building, s + '_max_building_height')
                   ]

        # Get buffers in decending size order and create column name lists
        sorted_buffers = sorted(buffer_sizes)[::-1]
        buffer_sizes = [str(s) for s in sorted_buffers]

        # Get buffer intersections
        buffer_intersection_query = self.__query_buffer_intersection(buffer_query, buffer_sizes).subquery()

        # Compose functions
        def sum_area(x, filt, lab):
            return func.coalesce(func.sum(func.ST_Area(func.Geography(x))).filter(filt), 0.0).label(lab)

        def max_cast(x, lab):
            return func.max(cast(x, Float)).label(lab)

        # Create a list of all the select functions for the query
        query_list = [buffer_intersection_query.c.id, buffer_intersection_query.c.lat, buffer_intersection_query.c.lon]

        for s in buffer_sizes:
            query_list = query_list + __summary_f_list(buffer_intersection_query, s)

        # Create the query and aggregate by interest point
        with self.open_session() as session:
            out = session.query(*query_list).\
                                group_by(buffer_intersection_query.c.id,
                                         buffer_intersection_query.c.lat,
                                         buffer_intersection_query.c.lon)

            if return_df:
                self.logger.info("Processing ukmap features... This may take some time")
                return pd.read_sql(out.statement, self.engine)
            else:
                return out

    @staticmethod
    def expand_static_feature_df(start_date, end_date, feature_df):

        start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

        ids = feature_df['id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date)
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=True)], names=["id", "time"])
        time_df = pd.DataFrame(index=index).reset_index()
        time_df_merged = time_df.merge(feature_df)

        return time_df_merged

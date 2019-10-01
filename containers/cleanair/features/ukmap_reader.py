"""
UKMap
"""
from datetime import datetime
import sqlalchemy
from sqlalchemy import func, and_, or_, cast, Float, insert
import pandas as pd
from dateutil import rrule
from ..databases import DBReader, features_tables, ukmap_table
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction


class ST_Collect(GenericFunction):
    name = 'ST_Collect'
    type = Geometry


class UKMapReader(DBReader):
    """
    Class for interfacing with the UKMap database table
    """
    def __init__(self, *args, **kwargs):
        # Initialise parent classes
        super().__init__(*args, **kwargs)

        # # Reflect the table
        # self.table = self.get_table_instance('ukmap', 'datasources')

        # laqn_tables.LAQNSite




        # List of filters to apply
        # Each list contains two tupes and an operator (or None). The first tuple contains table columns. The second contains values to filter those columns on.
        # The operator column can apply boolean operators to a zip of the first and second tuple

        self.col_filt_op = [[('feature_type',), ('Meseum',), None],
                       [('landuse',), ('Hospitals',), None],
                       [('feature_type',), ('Vegetated',), None],
                       [('feature_type', 'landuse',), ('Vegetated', 'Recreational open space'), and_],
                       [('feature_type',), ('Water',), None],
                       [('feature_type', 'feature_type'), ('Vegetated', 'Water'), or_]
                      ]


    def global_filter(self):
        """
        Returns the unique column filters in self.col_filt_op
        """

        a = [list(zip(*i[:2])) for i in self.col_filt_op]
        flat = [item for sublist in a for item in sublist]
        unique_filters = [i for i in set(flat)]

        return [[(i,) for i in j] + [None] for j in unique_filters]

    @property
    def feature_interest_points(self):
        with self.dbcnxn.open_session() as session:
            return [i[0] for i in session.query(features_tables.features_UKMAP.point_id).all()]

    @staticmethod
    def create_filter(table, filtop):
        """
        table can be a table object or Alias object (returned by Query.subquery())

        Pass a table and a list consiting of a tuple of columns, a tuple of filters and optionally an operator
        Returns a filter object
        """

        if isinstance(table, sqlalchemy.ext.declarative.api.DeclarativeMeta):
            col_obj = table
        elif isinstance(table, sqlalchemy.sql.selectable.Alias):
            col_obj = table.c

        columns, filt, operator = filtop
        col_filt_tuples = zip(columns, filt)

        # return col_filt_tuples

        args = [getattr(col_obj, tup[0]) == tup[1] for tup in col_filt_tuples]

        if operator:
            return operator(*args)
        return args[0]

    def query_buffer_intersection(self, buffer_query, buffer_cols):
        """
        Gets the intersection between buffers and the ukmap geoms
        """

        buffer_query = buffer_query.subquery()

        query_items = [buffer_query, ukmap_table.UKMap]

        # Get the intersection between the ukmap geometries and the largest buffer
        largest_intersection = func.ST_Force_2D(func.ST_Intersection(func.ST_MakeValid(
            ukmap_table.UKMap.geom), buffer_query.c['buffer_' + buffer_cols[0]])).label("intersect_" + buffer_cols[0])

        query_items = query_items + [largest_intersection]

        # If there are other buffers get the intersection between each buffer and the last intersection geomtry
        if len(buffer_cols) > 1:
            for buff in buffer_cols[1:]:
                next_intersection = func.ST_Force_2D(func.ST_Intersection(func.ST_MakeValid(
                    query_items[-1]), buffer_query.c['buffer_' + buff])).label("intersect_" + buff)
                query_items.append(next_intersection)

        # Filter intersecting geoms
        intersect_filters = [and_(func.ST_GeometryType(func.ST_MakeValid(ukmap_table.UKMap.geom)) == 'ST_MultiPolygon',
                   func.ST_Intersects(ukmap_table.UKMap.geom, buffer_query.c['buffer_' + buffer_cols[0]]))]

        # Filter to only data used by aggregation functions
        function_filters = [self.create_filter(ukmap_table.UKMap, cf) for cf in self.global_filter()]

        filters = [or_(*function_filters)] + intersect_filters

        # Create the query and apply filters
        with self.dbcnxn.open_session() as session:
            out = session.query(*query_items).filter(*filters)
            return out

    def query_features(self, buffer_query, buffer_sizes, return_type='insert'):
        """
        Process UKMap features and return as a dataframe or an sqlalchemy object

        Parameters
        ----------
        buffer_query: sqlalchemy query object
            A query object returned by the .query_interest_point_buffers() methods on objects with interest points
        buffer_sizes: list
            A list of buffer sizes
        return_type: str, optional
            'df': dataframe
            'query': query object
            'insert': Insert into the ukmap features table
        """
        if not isinstance(buffer_sizes, list):
            raise TypeError("buffer_sizes object must be a list")

        def __intersected_col_name(size):
            return 'intersect_' + str(size)

        def sum_area(geom, filt, lab):
            return func.coalesce(func.sum(func.ST_Area(func.Geography(geom))).filter(filt), 0.0).label(lab)

        def max_cast(geom, lab):
            return func.max(cast(geom, Float)).label(lab)

        def __summary_f_list(subquery, buffer_size):
            """
            For a given intersected geometry, create summary functions and tag with appropriate label
            """
            geom = subquery.c[__intersected_col_name(buffer_size)]

            function_list = [
                            [sum_area, subquery.c.feature_type == 'Museum', 'total_museum_area_' + buffer_size],
                            [sum_area, subquery.c.landuse == 'Hospitals', 'total_hospital_area_'+ buffer_size],
                            [sum_area, subquery.c.feature_type == 'Vegetated',  'total_grass_area_'+ buffer_size],
                            [sum_area, and_(subquery.c.feature_type == 'Vegetated',
                                                        subquery.c.landuse == 'Recreational open space'),
                                            'total_park_area'+ buffer_size],
                            [sum_area, subquery.c.feature_type == 'Water', 'total_water_area_'+ buffer_size],
                            [sum_area, or_(subquery.c.feature_type == 'Vegetated',
                                                    subquery.c.feature_type == 'Water'), 'total_flat_area_'+ buffer_size]
                            ]

            agg_funcs = [f(geom, filt, lab) for f, filt, lab in function_list]
            agg_funcs.append(max_cast(subquery.c.calculated_height_of_building, 'max_building_height_'+ buffer_size))
            # agg_funcs.append(func.ST_GeomFromEWKB(ST_Collect(geom)).label('geom_' + buffer_size))
            return agg_funcs

        # Get buffers in decending size order and create column name lists
        sorted_buffers = sorted(buffer_sizes)[::-1]
        buffer_sizes = [str(s) for s in sorted_buffers]

        # Get buffer intersections
        buffer_intersection_subquery = self.query_buffer_intersection(buffer_query, buffer_sizes).subquery()

        # Create a list of all the select functions for the query
        query_list = [buffer_intersection_subquery.c.point_id,
                     buffer_intersection_subquery.c.source]

        for size in buffer_sizes:
            query_list = query_list + __summary_f_list(buffer_intersection_subquery, size)

        # Create the query and aggregate by interest point
        with self.dbcnxn.open_session() as session:
            out = session.query(*query_list).group_by(buffer_intersection_subquery.c.point_id,
                                                      buffer_intersection_subquery.c.source)
            if return_type == 'df':
                self.logger.info("Processing ukmap features... This may take some time")
                return pd.read_sql(out.statement, self.dbcnxn.engine)

            elif return_type == 'insert':
                sel = out.subquery().select()
                ins = insert(features_tables.features_UKMAP).from_select([c.key for c in features_tables.features_UKMAP.__table__.columns], sel)
                with self.dbcnxn.engine.connect() as cnxn:
                    self.logger.info("Calculating and inserting features into database")
                    cnxn.execute(ins)
                    self.logger.info("Insertion finished")
            return out


    @staticmethod
    def expand_static_feature_df(start_date, end_date, feature_df):
        """
        Returns a new dataframe with UKMap features merged with hourly timestamps between start_date and end_date
        """
        start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

        ids = feature_df['id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date)
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=True)], names=["id", "time"])
        time_df = pd.DataFrame(index=index).reset_index()
        time_df_merged = time_df.merge(feature_df)

        return time_df_merged

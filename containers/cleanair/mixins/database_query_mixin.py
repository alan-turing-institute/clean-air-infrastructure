"""
Mixin for useful database queries
"""

from sqlalchemy import func
from sqlalchemy import null, literal, and_
from ..decorators import db_query
from ..databases.tables import (LondonBoundary, IntersectionValue, IntersectionValueDynamic, MetaPoint,
                                AQESite, LAQNSite, LAQNReading, AQEReading)
from ..loggers import get_logger


class DBQueryMixin():
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    @db_query
    def get_available_static_features(self):
        """Return available static features from the CleanAir database
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(IntersectionValue.feature_name).distinct(IntersectionValue.feature_name)

            return feature_types_q

    @db_query
    def get_available_dynamic_features(self, start_date, end_date):
        """Return a list of the available dynamic features in the database.
            Only returns features that are available between start_date and end_date
        """

        with self.dbcnxn.open_session() as session:

            available_dynamic_sq = session.query(IntersectionValueDynamic.feature_name,
                                                 func.min(IntersectionValueDynamic.measurement_start_utc).label(
                                                     'min_date'),
                                                 func.max(IntersectionValueDynamic.measurement_start_utc).label('max_date')) \
                .group_by(IntersectionValueDynamic.feature_name).subquery()

            available_dynamic_q = session.query(available_dynamic_sq).filter(and_(available_dynamic_sq.c['min_date'] <= start_date,
                                                                                  available_dynamic_sq.c['max_date'] >= end_date))

            return available_dynamic_q

    @db_query
    def get_available_sources(self):
        """Return the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return feature_types_q

    @db_query
    def get_available_interest_points(self, sources):
        """Return the available interest points for a list of sources, excluding any LAQN or AQE sites that are closed. Only returns points withing the London boundary
        args:
            sources: A list of sources to include
        """

        bounded_geom = self.query_london_boundary()
        base_query_columns = [MetaPoint.id.label('point_id'),
                              MetaPoint.source.label('source'),
                              MetaPoint.location.label('location'),
                              func.ST_X(MetaPoint.location).label('lon'),
                              func.ST_Y(MetaPoint.location).label('lat')
                              ]

        with self.dbcnxn.open_session() as session:

            remaining_sources_q = session.query(*base_query_columns,
                                                null().label("date_opened"),
                                                null().label("date_closed"),
                                                ).filter(MetaPoint.source.in_([source for source in sources if source not in ['laqn', 'aqe']]),
                                                         MetaPoint.location.ST_Within(bounded_geom))

            aqe_sources_q = session.query(*base_query_columns,
                                          AQESite.date_opened,
                                          AQESite.date_closed
                                          ).join(AQESite, isouter=True).filter(MetaPoint.source.in_(['aqe']),
                                                                               MetaPoint.location.ST_Within(bounded_geom))

            laqn_sources_q = session.query(*base_query_columns,
                                           LAQNSite.date_opened,
                                           LAQNSite.date_closed
                                           ).join(LAQNSite, isouter=True).filter(MetaPoint.source.in_(['laqn']),
                                                                                 MetaPoint.location.ST_Within(bounded_geom))

            all_sources_sq = remaining_sources_q.union(aqe_sources_q, laqn_sources_q).subquery()

            # Remove any sources where there is a closing date
            all_sources_q = session.query(all_sources_sq).filter(all_sources_sq.c.date_closed == None)

        return all_sources_q

    @db_query
    def get_laqn_readings(self, start_date, end_date):

        with self.dbcnxn.open_session() as session:
            laqn_reading_q = session.query(LAQNReading.measurement_start_utc,
                                           LAQNReading.species_code,
                                           LAQNReading.value,
                                           LAQNSite.point_id,
                                           literal('laqn').label('source')).join(LAQNSite)
            laqn_reading_q = laqn_reading_q.filter(LAQNReading.measurement_start_utc >= start_date,
                                                   LAQNReading.measurement_start_utc < end_date)
            return laqn_reading_q

    @db_query
    def get_aqe_readings(self, start_date, end_date):

        with self.dbcnxn.open_session() as session:
            aqe_reading_q = session.query(AQEReading.measurement_start_utc,
                                          AQEReading.species_code,
                                          AQEReading.value,
                                          AQESite.point_id,
                                          literal('aqe').label('source')).join(AQESite)
            aqe_reading_q = aqe_reading_q.filter(AQEReading.measurement_start_utc >= start_date,
                                                 AQEReading.measurement_start_utc < end_date)
            return aqe_reading_q

        # def query_sensor_site_info(self, source):
        #     """Query the database to get the site info for a datasource (e.g. 'laqn', 'aqe') and return a dataframe

        #     args:
        #         source: The sensor source('laqn' or 'aqe')
        #     """
        #     interest_point_q = self.get_available_interest_points(source=[source])
        #     interest_point_sq = interest_point_q.subquery()

        #     if source == 'laqn':
        #         INFOSite = LAQNSite
        #     elif source == 'aqe':
        #         INFOSite = AQESite

        #     with self.dbcnxn.open_session() as session:

        #         join_info_site_q = session.query(interest_point_sq,
        #                                          INFOSite.site_code,
        #                                          INFOSite.date_opened,
        #                                          INFOSite.date_closed).join(INFOSite, isouter=True)

        #         interest_point_join_df = pd.read_sql(join_info_site_q.statement,
        #                                              join_info_site_q.session.bind)

        #         interest_point_join_df['point_id'] = interest_point_join_df['point_id'].astype(str)
        #         interest_point_df = interest_point_join_df.groupby(['point_id',
        #                                                             'source',
        #                                                             'lon',
        #                                                             'lat']).agg({'date_opened': 'min',
        #                                                                          'date_closed': 'max'}).reset_index()

        #         return interest_point_df

        # def sensor_data_status(self, start_date, end_date, source, species):
        #     """Return a dataframe which gives the status of sensor readings for a particular source and species between
        #     the start_date(inclusive) and end_date.
        #     """

        #     def categorise(res):
        #         if not res['open']:
        #             status = 'Closed'
        #         elif res['open'] and not res['missing_reading']:
        #             status = 'OK'
        #         else:
        #             status = 'Missing'
        #         return status

        #     # Get interest points with site open and site closed dates and then expand with time
        #     interest_point_df = self.query_sensor_site_info(source=source)
        #     time_df_merged = self.__expand_time(start_date, end_date, interest_point_df)

        #     # Check if an interest_point was open at all times
        #     time_df_merged['open'] = (
        #         (time_df_merged['date_opened'] <= time_df_merged['measurement_start_utc']) &
        #         ((time_df_merged['measurement_start_utc'] < time_df_merged['date_closed']) | pd.isnull(
        #             time_df_merged['date_closed']))
        #     )

        #     # Merge sensor readings onto interst points
        #     sensor_readings = self.__get_sensor_readings(start_date, end_date, sources=[source], species=[species])
        #     time_df_merged = pd.merge(
        #         time_df_merged, sensor_readings, how='left', on=[
        #             'point_id', 'measurement_start_utc', 'epoch', 'source'])
        #     time_df_merged['missing_reading'] = pd.isnull(time_df_merged[species])

        #     # Categorise as either OK (has a reading), closed (sensor closed)
        #     # or missing (no data in database even though sensor is open)
        #     time_df_merged['category'] = time_df_merged.apply(categorise, axis=1)

        #     def set_instance(group):
        #         """Categorise each row as an instance, where a instance increments
        #         if the difference from the preceeding timestamp is > 1h
        #         """

        #         group['offset_time'] = group['measurement_start_utc'].diff() / pd.Timedelta(hours=1)
        #         group.at[group.index[0], 'offset_time'] = 1.
        #         group['instance'] = (group['offset_time'].astype(int) - 1).apply(lambda x: min(1, x)).cumsum()
        #         return group

        #     time_df_merged_instance = time_df_merged.groupby(['point_id', 'category']).apply(set_instance)
        #     time_df_merged_instance['measurement_end_utc'] = (time_df_merged_instance['measurement_start_utc'] +
        #                                                       pd.DateOffset(hours=1))

        #     # Group consecutive readings of same category
        #     time_df_merged_instance = time_df_merged_instance.groupby(['point_id', 'category', 'instance']) \
        #         .agg({'measurement_start_utc': 'min', 'measurement_end_utc': 'max'}) \
        #         .reset_index()

        #     return time_df_merged_instance

        # @staticmethod
        #     def show_vis(sensor_status_df, title='Sensor data'):
        #         """Show a plotly gantt chart of a dataframe returned by self.sensor_data_status"""

        #         gant_df = sensor_status_df[['point_id', 'measurement_start_utc', 'measurement_end_utc', 'category']].rename(
        #             columns={'point_id': 'Task',
        #                      'measurement_start_utc': 'Start',
        #                      'measurement_end_utc': 'Finish',
        #                      'category': 'Resource'})

        #         # Create the gant chart
        #         colors = dict(OK='#76BA63',
        #                       Missing='#BA6363',
        #                       Closed='#828282',)

        #         fig = ff.create_gantt(
        #             gant_df,
        #             group_tasks=True,
        #             colors=colors,
        #             index_col='Resource',
        #             show_colorbar=True,
        #             showgrid_x=True,
        #             bar_width=0.38)
        #         fig['layout'].update(autosize=True, height=10000, title=title)
        #         fig.show()

"""
Vizualise available sensor data for a model fit
"""
import pandas as pd
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from sqlalchemy import literal, func
import plotly.figure_factory as ff
from ..databases.tables import IntersectionValue, LAQNSite, LAQNReading, MetaPoint, AQESite, AQEReading, ModelResult
from ..databases import DBReader, DBWriter
from ..loggers import get_logger


class ModelData(DBReader, DBWriter):
    """Class to query sensor readings and features from the cleanair database and format for model fitting"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Dataframe with model fit results
        self.fit_df = None

    def __get_interest_points(self, source='laqn'):
        """Get all interest points for a given source"""

        with self.dbcnxn.open_session() as session:

            interest_point_query = session.query(
                MetaPoint.id.label('point_id'),
                MetaPoint.source,
                MetaPoint.location,
                func.ST_X(MetaPoint.location).label('lon'),
                func.ST_Y(MetaPoint.location).label('lat')
                ).filter(MetaPoint.source == source)

            return interest_point_query

    def list_available_features(self):
        """Return a dataframe with the available features in the database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(IntersectionValue.feature_name).distinct(IntersectionValue.feature_name)

            return pd.read_sql(feature_types_q.statement,
                               feature_types_q.session.bind)

    def query_sensor_site_info(self, source):
        """Get the site info for a datasource (e.g. 'laqn', 'aqe')"""
        interest_point_q = self.__get_interest_points(source=source)
        interest_point_sq = interest_point_q.subquery()

        if source == 'laqn':
            INFOSite = LAQNSite
        elif source == 'aqe':
            INFOSite = AQESite

        with self.dbcnxn.open_session() as session:

            join_info_site_q = session.query(interest_point_sq,
                                             INFOSite.site_code,
                                             INFOSite.date_opened,
                                             INFOSite.date_closed).join(INFOSite, isouter=True)

            interest_point_join_df = pd.read_sql(join_info_site_q.statement,
                                                 join_info_site_q.session.bind)

            interest_point_join_df['point_id'] = interest_point_join_df['point_id'].astype(str)
            interest_point_df = interest_point_join_df.groupby(['point_id',
                                                                'source',
                                                                'lon',
                                                                'lat']).agg({'date_opened': 'min',
                                                                             'date_closed': 'max'}).reset_index()

            return interest_point_df

    def sensor_data_status(self, start_date, end_date, source='laqn', species='NO2'):
        """Return a dataframe which gives the status of sensor readings for a particular source and species between
        the start_date (inclusive) and end_date.
        """

        def categorise(res):
            if not res['open']:
                status = 'Closed'
            elif res['open'] and not res['missing_reading']:
                status = 'OK'
            else:
                status = 'Missing'
            return status

        # Get interest points with site open and site closed dates and then expand with time
        interest_point_df = self.query_sensor_site_info(source=source)
        time_df_merged = self.expand_time(start_date, end_date, interest_point_df)

        # Check if an interest_point was open at all times
        time_df_merged['open'] = (
            (time_df_merged['date_opened'] <= time_df_merged['measurement_start_utc']) &
            ((time_df_merged['measurement_start_utc'] < time_df_merged['date_closed']) | pd.isnull(
                time_df_merged['date_closed']))
        )

        # Merge sensor readings onto interst points
        sensor_readings = self.get_sensor_readings(start_date, end_date, sources=[source], species=[species])
        time_df_merged = pd.merge(
            time_df_merged, sensor_readings, how='left', on=[
                'point_id', 'measurement_start_utc', 'epoch', 'source'])
        time_df_merged['missing_reading'] = pd.isnull(time_df_merged[species])

        # Categorise as either OK (has a reading), closed (sensor closed)
        # or missing (no data in database even though sensor is open)
        time_df_merged['category'] = time_df_merged.apply(categorise, axis=1)

        def set_instance(group):
            """categorise each row as an instance, where a instance increments
            if the difference from the preceeding timestamp is >1h"""

            group['offset_time'] = group['measurement_start_utc'].diff() / pd.Timedelta(hours=1)
            group.at[group.index[0], 'offset_time'] = 1.
            group['instance'] = (group['offset_time'].astype(int) - 1).apply(lambda x: min(1, x)).cumsum()
            return group

        time_df_merged_instance = time_df_merged.groupby(['point_id', 'category']).apply(set_instance)
        time_df_merged_instance['measurement_end_utc'] = (time_df_merged_instance['measurement_start_utc'] +
                                                          pd.DateOffset(hours=1))

        # Group consecutive readings of same category
        time_df_merged_instance = time_df_merged_instance.groupby(['point_id', 'category', 'instance']) \
            .agg({'measurement_start_utc': 'min', 'measurement_end_utc': 'max'}) \
            .reset_index()

        return time_df_merged_instance

    @staticmethod
    def show_vis(sensor_status_df, title='Sensor data'):
        """Show a plotly gantt chart of a dataframe returned by self.sensor_data_status"""

        gant_df = sensor_status_df[['point_id', 'measurement_start_utc', 'measurement_end_utc', 'category']].rename(
            columns={'point_id': 'Task',
                     'measurement_start_utc': 'Start',
                     'measurement_end_utc': 'Finish',
                     'category': 'Resource'})

        # Create the gant chart
        colors = dict(OK='#76BA63',
                      Missing='#BA6363',
                      Closed='#828282',)

        fig = ff.create_gantt(
            gant_df,
            group_tasks=True,
            colors=colors,
            index_col='Resource',
            show_colorbar=True,
            showgrid_x=True,
            bar_width=0.38)
        fig['layout'].update(autosize=True, height=10000, title=title)
        fig.show()

    def select_static_features(self, sources=None, point_ids=None):
        """Select static features and join with metapoint data"""

        with self.dbcnxn.open_session() as session:

            feature_query = session.query(IntersectionValue)
            interest_point_query = session.query(
                MetaPoint.id.label('point_id'),
                MetaPoint.source,
                MetaPoint.location,
                func.ST_X(MetaPoint.location).label('lon'),
                func.ST_Y(MetaPoint.location).label('lat')
                ).filter(MetaPoint.source.in_(sources))

            if point_ids is not None:
                interest_point_query = interest_point_query.filter(MetaPoint.id.in_(point_ids))

            # Select into into dataframes
            features_df = pd.read_sql(feature_query.statement,
                                      feature_query.session.bind)

            interest_point_df = pd.read_sql(interest_point_query.statement,
                                            interest_point_query.session.bind).set_index('point_id')

            # Reshape features df (make wide)
            features_df = features_df.pivot(index='point_id', columns='feature_name').reset_index()
            features_df.columns = ['point_id'] + ['_'.join(col).strip() for col in features_df.columns.values[1:]]
            features_df = features_df.set_index('point_id')

            # Set index types to str
            features_df.index = features_df.index.astype(str)
            interest_point_df.index = interest_point_df.index.astype(str)

            # Inner join the MetaPoint and IntersectionValue data
            df_joined = pd.concat([interest_point_df, features_df], axis=1, sort=False, join='inner')

            return df_joined.reset_index()

    @staticmethod
    def expand_time(start_date, end_date, feature_df):
        """
        Returns a new dataframe with static features merged with
        hourly timestamps between start_date (inclusive) and end_date
        """
        start_date = isoparse(start_date).date()
        end_date = isoparse(end_date).date()

        ids = feature_df['point_id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date - relativedelta(hours=+1))
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=False)],
                                           names=["point_id", "measurement_start_utc"])
        time_df = pd.DataFrame(index=index).reset_index()
        time_df_merged = time_df.merge(feature_df)
        time_df_merged['epoch'] = time_df_merged['measurement_start_utc'].apply(lambda x: x.timestamp())
        return time_df_merged

    def __get_laqn_readings(self, start_date, end_date):

        with self.dbcnxn.open_session() as session:
            query = session.query(LAQNReading.measurement_start_utc,
                                  LAQNReading.species_code,
                                  LAQNReading.value,
                                  LAQNSite.point_id,
                                  literal('laqn').label('source')).join(LAQNSite)
            query = query.filter(LAQNReading.measurement_start_utc >= start_date,
                                 LAQNReading.measurement_start_utc < end_date)
            return query

    def __get_aqe_readings(self, start_date, end_date):

        with self.dbcnxn.open_session() as session:
            query = session.query(AQEReading.measurement_start_utc,
                                  AQEReading.species_code,
                                  AQEReading.value,
                                  AQESite.point_id,
                                  literal('aqe').label('source')).join(AQESite)
            query = query.filter(AQEReading.measurement_start_utc >= start_date,
                                 AQEReading.measurement_start_utc < end_date)
            return query

    def get_sensor_readings(self, start_date, end_date, sources=None, species=None):
        """Get sensor readings for the sources between the start_date (inclusive) and end_date"""

        self.logger.info("Getting sensor readings for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                         sources, species, start_date, end_date)

        start_date_ = isoparse(start_date)
        end_date_ = isoparse(end_date)

        sensor_dfs = []
        if 'laqn' in sources:
            sensor_q = self.__get_laqn_readings(start_date_, end_date_)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        if 'aqe' in sources:
            sensor_q = self.__get_aqe_readings(start_date_, end_date_)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        sensor_df = pd.concat(sensor_dfs, axis=0)
        sensor_df['point_id'] = sensor_df['point_id'].astype(str)
        sensor_df['epoch'] = sensor_df['measurement_start_utc'].apply(lambda x: x.timestamp())
        sensor_df = sensor_df.pivot_table(
            index=[
                'point_id',
                'source',
                'measurement_start_utc',
                'epoch'],
            columns=['species_code'],
            values='value')

        return sensor_df[species].reset_index()

    def get_model_features(self, start_date, end_date, sources=None):
        """
        Query the database for model features
        """
        self.logger.info("Getting features for sources: %s, from %s (inclusive) to %s (exclusive)",
                         sources, start_date, end_date)

        static_features = self.select_static_features(sources=sources)
        static_features_expand = self.expand_time(start_date, end_date, static_features)

        return static_features_expand

    def get_model_inputs(self, start_date, end_date, sources=None, species=None):
        """
        Query the database for model inputs. Returns all features.
        """

        # Get sensor readings and summary of availible data from start_date (inclusive) to end_date
        readings = self.get_sensor_readings(start_date, end_date, sources=sources, species=species)
        static_features_expand = self.get_model_features(start_date, end_date, sources)
        model_data = pd.merge(static_features_expand,
                              readings,
                              on=['point_id', 'measurement_start_utc', 'epoch', 'source'],
                              how='left')
        return model_data

    def update_model_results_table(self, data_df):
        """Update the model results table, passing a dataframe created by ModelFitting.predict()"""
        self.fit_df = data_df
        self.update_remote_tables()

    def update_remote_tables(self):
        """Update the model results table with the model results"""

        record_cols = ['fit_start_time', 'point_id', 'measurement_start_utc', 'predict_mean', 'predict_var']
        df_cols = self.fit_df.columns
        for col in record_cols:
            if col not in df_cols:
                raise AttributeError("The data frame must contain the following columns: {}".format(record_cols))

        upload_records = self.fit_df[record_cols].to_dict('records')

        with self.dbcnxn.open_session() as session:
            self.add_records(session, upload_records, flush=True, table=ModelResult)

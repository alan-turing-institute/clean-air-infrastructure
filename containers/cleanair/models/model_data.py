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


class ModelDataReader(DBReader, DBWriter):
    """Read data from multiple database tables in order to get data for model fitting"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

    def __check_features_in_database(self, features):
        """Check that all requested features exist in the database"""

        available_features = self.list_available_features()
        unavailable_features = []

        for feature in features:
            feature_name_no_buff = "_".join(feature.split("_")[2:])
            if feature_name_no_buff not in available_features:
                unavailable_features.append(feature)

        if unavailable_features:
            raise AttributeError("The following features are not available the cleanair database: {}"
                                 .format(unavailable_features))

    def __check_sources_in_database(self, sources):
        """Check that sources are available in the database

        args:
            sources: A list of sources
        """

        available_sources = self.list_available_sources()
        unavailable_sources = []

        for source in sources:
            if source not in available_sources:
                unavailable_sources.append(source)

        if unavailable_sources:
            raise AttributeError("The following sources are not available the cleanair database: {}"
                                 .format(unavailable_sources))

    def list_available_features(self):
        """Return a list of the available features in the database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(IntersectionValue.feature_name).distinct(IntersectionValue.feature_name)

            return pd.read_sql(feature_types_q.statement,
                               feature_types_q.session.bind)['feature_name'].tolist()

    def list_available_sources(self):
        """Return a list of the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return pd.read_sql(feature_types_q.statement,
                               feature_types_q.session.bind)['source'].tolist()

    def __get_interest_points(self, source='laqn'):
        """Query the database to get all interest points for a given source and return a query object"""

        with self.dbcnxn.open_session() as session:

            interest_point_query = session.query(
                MetaPoint.id.label('point_id'),
                MetaPoint.source,
                MetaPoint.location,
                func.ST_X(MetaPoint.location).label('lon'),
                func.ST_Y(MetaPoint.location).label('lat')
                ).filter(MetaPoint.source == source)

            return interest_point_query

    def query_sensor_site_info(self, source):
        """Query the database to get the site info for a datasource (e.g. 'laqn', 'aqe') and return a dataframe

        args:
            source: The sensor source ('laqn' or 'aqe')
        """
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
        time_df_merged = self.__expand_time(start_date, end_date, interest_point_df)

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
            """Categorise each row as an instance, where a instance increments
            if the difference from the preceeding timestamp is >1h
            """

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
    
    def show_vis(self, sensor_status_df, title='Sensor data'):
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
        """Query the database for static features and join with metapoint data

        args:
            source: A list of sources (e.g. 'laqn', 'aqe') to include. Default will include all sources
            point_ids: A list if interest point ids. Default to all ids"""

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

    def __expand_time(self, start_date, end_date, feature_df):
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

        self.logger.debug("Getting sensor readings for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
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
        static_features = self.select_static_features(sources=sources)
        static_features_expand = self.__expand_time(start_date, end_date, static_features)

        return static_features_expand

    def get_model_inputs(self, start_date, end_date, sources=None, species=None):
        """
        Query the database to get inputs for model fitting. Returns all features.

        ags:
            start_date: An iso datetime (yyyy-mm-ddTHH:MM:SS) to get data from (inclusive)
            end_date: An iso datetime (yyyy-mm-ddTHH:MM:SS) to get data from (exclusive)
            sources: A list of sources (e.g 'laqn', 'aqe' to get data for)
            species: A list of species to get data for (e.g. 'NO2')
        """

        self.logger.debug("Getting model inputs for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                         sources, species, start_date, end_date)

        # Get sensor readings and summary of availible data from start_date (inclusive) to end_date
        readings = self.get_sensor_readings(start_date, end_date, sources=sources, species=species)        
        static_features_expand = self.get_model_features(start_date, end_date, sources)

        self.logger.debug("Merging sensor data and model features")

        model_data = pd.merge(static_features_expand,
                              readings,
                              on=['point_id', 'measurement_start_utc', 'epoch', 'source'],
                              how='left')
        return model_data

    def update_model_results_table(self, predict_data_dict, Y_pred, model_fit_info):

        # # Create new dataframe with predictions
        predict_df = pd.DataFrame(index=predict_data_dict['index'])
        predict_df['predict_mean'] = Y_pred[:,0]
        predict_df['predict_var'] = Y_pred[:,1]
        predict_df['fit_start_time'] = self.fit_start_time
        predict_df['tag'] = self.tag

        # # Concat the predictions with the predict_df
        self.normalised_test_data_df = pd.concat([self.normalised_test_data_df, predict_df], axis=1, ignore_index=False)

    def update_remote_tables(self):
        """Update the model results table with the model results"""

        record_cols = ['tag', 'fit_start_time', 'point_id', 'measurement_start_utc', 'predict_mean', 'predict_var']
        df_cols = elf.normalised_test_data_df
        for col in record_cols:
            if col not in df_cols:
                raise AttributeError("The data frame must contain the following columns: {}".format(record_cols))

        upload_records = self.normalised_test_data_df[record_cols].to_dict('records')

        with self.dbcnxn.open_session() as session:
            self.add_records(session, upload_records, flush=True, table=ModelResult)

class ModelData(ModelDataReader):
    """Class to prepare data for model fitting"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Attributes created by self.initialise
        self.x_names = None
        self.y_names = None
        self.training_data_df = None
        self.test_data_df = None
        self.normalised_training_data_df = None
        self.normalise_test_data_df = None

    def initialise(self, config):
        """
        Initialise the ModelData object with a config file
        args:
            config: A config dictionary

            Example config:
                {
                "train_start_date": "2019-11-01T00:00:00",
                "train_end_date": "2019-11-30T00:00:00",
                "pred_start_date": "2019-11-01T00:00:00",
                "pred_end_date": "2019-11-30T00:00:00",

                "train_sources": ["laqn", "aqe"],
                "pred_sources": ["laqn", "aqe"],
                "species": ["NO2"],
                "features": "all",
                "norm_by": "laqn",

                "model_type": "svgp",
                "tag": "production"
                }
        """

        # Validate the configuration
        self.__validate_config(config)

        # Set attributes from validated config
        self.train_start_date = config['train_start_date']
        self.train_end_date = config['train_end_date']
        self.pred_start_date = config['pred_start_date']
        self.pred_end_date = config['pred_end_date']
        self.train_sources = config['train_sources']
        self.pred_sources = config['pred_sources']
        self.species = config['species']

        if config['features'] == 'all':
            feature_names = self.list_available_features()
            buff_size = [1000, 500, 200, 100, 10]            
            config['features'] = ["value_{}_{}".format(buff, name) for buff in buff_size for name in feature_names]
            self.logger.info("Features 'all' replaced with available features: {}".format(config['features']))
        
        self.features = config['features'] 
        self.norm_by = config['norm_by']       
        self.model_type = config['model_type']
        self.tag = config['tag']

        # Column names for X and Y
        self.x_names = ["epoch", "lat", "lon"] + self.features
        self.y_names = self.species      

        # Get model data from database using parent class ModelDataReader
        self.training_data_df = self.get_model_inputs(self.train_start_date, self.train_end_date, self.train_sources, self.species)
        self.normalised_training_data_df = self.__normalise_data(self.training_data_df)

        self.test_data_df = self.get_model_features(self.pred_start_date, self.pred_end_date, self.pred_sources)        
        self.normalised_test_data_df = self.__normalise_data(self.test_data_df)

    def __validate_config(self, config):

        config_keys = ["train_start_date",
                       "train_end_date",
                       "pred_start_date",
                       "pred_end_date",
                       "train_sources",
                       "pred_sources",
                       "species",
                       "features",
                       "norm_by",
                       "model_type",
                       'tag',]

        valid_models = ['svgp',]

        self.logger.info("Validating config")

        # Check keys present
        for key in config.keys():
            if key not in config_keys:
                raise AttributeError("Config dictionary does not contain key: {}".format(key))
        
        # Check features are available        
        if config['features'] == 'all':
            features = self.list_available_features()
            if not features:
                raise AttributeError("There are no features in the database. Run feature extraction first")
        else:
            self.logger.debug("Checking requested features are availble in database")
            self._ModelDataReader__check_features_in_database(config['features'])

        # Check sources are available
        train_sources = config['train_sources'] 
        self.logger.debug("Checking requested sources for training are availble in database")
        self._ModelDataReader__check_sources_in_database(train_sources)

        # Check sources are available
        pred_sources = config['pred_sources'] 
        self.logger.debug("Checking requested sources for prediction are availble in database")
        self._ModelDataReader__check_sources_in_database(pred_sources)

        # Check model type is valid
        if config['model_type'] not in valid_models:
            raise AttributeError("{} is not a valid model type. Use one of the following: {}".format(config['model_type'], 
                                                                                                     valid_models))
        self.logger.info("Validate config complete")

    @property
    def x_names_norm(self):
        """Get the normalised x names"""
        return [x + '_norm' for x in self.x_names]

    @property
    def norm_stats(self):
        """Get the mean and sd used for data normalisation"""
        norm_mean = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].mean(axis=0)
        norm_std = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].std(axis=0)
        return norm_mean, norm_std

    def __normalise_data(self, data_df):
        """Normalise the x columns"""
        norm_mean, norm_std = self.norm_stats
        # Normalise the data
        data_df[self.x_names_norm] = (data_df[self.x_names] - norm_mean) / norm_std
        return data_df

    def __get_model_data_arrays(self, data_df, return_y, dropna=True):
        """Return a dictionary of data arrays for model fitting.
        The returned dictionary includes and index to allow model predictions
        to be appended to dataframes (required when dropna is used)"""

        if return_y:
            data_subset = data_df[self.x_names_norm + self.y_names]
        else:
            data_subset = data_df[self.x_names_norm]

        if dropna:
            data_subset = data_subset.dropna()  # Must have complete dataset
            n_dropped_rows = data_df.shape[0] - data_subset.shape[0]
            self.logger.warning("Dropped %s rows out of %s from the dataframe", n_dropped_rows, data_df.shape[0])

        data_dict = {'X': data_subset[self.x_names_norm].values, 'index': data_subset[self.x_names_norm].index}

        if return_y:
            data_dict['Y'] = data_subset[self.y_names].values

        return data_dict

    def get_training_data_arrays(self, dropna=True):
        """The the training data arrays.

        args:
            dropna: Drop any rows which contain NaN
        """
        return self.__get_model_data_arrays(self.normalised_training_data_df, return_y=True, dropna=dropna)

    def get_test_data_arrays(self, return_y=False, dropna=True):
        """The the test data arrays.

        args:
            return_y: Return the sensor data if in the database for the prediction dates
            dropna: Drop any rows which contain NaN
        """
        return self.__get_model_data_arrays(self.normalised_test_data_df, return_y=False, dropna=dropna)

"""
Vizualise available sensor data for a model fit
"""
import json
import os
import pandas as pd
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from sqlalchemy import literal, func, null
import plotly.figure_factory as ff
from ..databases.tables import (IntersectionValue, IntersectionValueDynamic, LAQNSite,
                                LAQNReading, MetaPoint, AQESite,
                                AQEReading, ModelResult, SatelliteForecastReading, SatelliteDiscreteSite)
from ..databases import DBWriter
from ..mixins import DBQueryMixin
from ..loggers import get_logger


class ModelData(DBWriter, DBQueryMixin):
    """Read data from multiple database tables in order to get data for model fitting"""

    def __init__(self, config=None, config_dir=None, **kwargs):
        """
        Initialise the ModelData object with a config file
        args:
            config: A config dictionary
            config_dir: A directory containing config files (created by ModelData.save_config_state())

            Example config:
                {
                "train_start_date": "2019-11-01T00:00:00",
                "train_end_date": "2019-11-30T00:00:00",
                "pred_start_date": "2019-11-01T00:00:00",
                "pred_end_date": "2019-11-30T00:00:00",

                "train_sources": ["laqn", "aqe"],
                "pred_sources": ["laqn", "aqe"],
                "train_interest_points": ['point_id1', 'point_id2'],
                'train_satellite_interest_points': ['point_id1', 'point_id2']
                "pred_interest_points": ['point_id1', 'point_id2'],
                "species": ["NO2"],
                "features": "all",
                "norm_by": "laqn",

                "model_type": "svgp",
                "tag": "production"
                }
        """

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        if not (config or config_dir):
            raise ValueError("Either config or config_dir must be supplied as arguments")

        if config:
            # Validate the configuration
            self.__validate_config(config)
            self.config = self.__generate_full_config(config)

            # Get training and prediciton data frames
            self.training_data_df = self.get_training_data_inputs()
            self.normalised_training_data_df = self.__normalise_data(self.training_data_df)

            self.pred_data_df = self.get_pred_data_inputs()
            self.normalised_pred_data_df = self.__normalise_data(self.pred_data_df)

            # Process satellite data
            if self.config['include_satellite']:
                self.training_satellite_data_x, self.training_satellite_data_y = self.get_training_satellite_inputs()

                self.training_satellite_data_x = self.training_satellite_data_x.sort_values(
                    ['box_id', 'measurement_start_utc', 'point_id'])[['point_id', 'box_id'] + config['x_names']]

                self.training_satellite_data_y = self.training_satellite_data_y.sort_values(
                    ['box_id', 'measurement_start_utc'])

        else:
            self.restore_config_state(config_dir)

    def save_config_state(self, dir_path, dropna_training=False, dropna_pred=False):
        """Save the full configuration and training/prediction data to disk:

        args:
            dir_path: Directory path in which to save the config files
            dropna_training : Drop rows AND columns with NaNs from normalised_training_data_df before saving to csv.
            dropna_pred : Drop rows AND columns with NaNs from normalised_pred_data_df before saving to csv.
        """

        # Create a new directory
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        # Write the files to the directory
        if dropna_training:
            # drop na columns first, then drop na rows
            self.normalised_training_data_df.dropna(axis=1).dropna().to_csv(os.path.join(dir_path, 'normalised_training_data.csv'))
        else:
            self.normalised_training_data_df.to_csv(os.path.join(dir_path, 'normalised_training_data.csv'))

        if dropna_pred:
            # drop na columns first, then drop na rows
            self.normalised_pred_data_df.dropna(axis=1).dropna().to_csv(os.path.join(dir_path, 'normalised_pred_data.csv'))
        else:
            self.normalised_pred_data_df.to_csv(os.path.join(dir_path, 'normalised_pred_data.csv'))

        with open(os.path.join(dir_path, 'config.json'), 'w') as config_f:
            json.dump(self.config, config_f, sort_keys=True, indent=4)

        self.logger.info("State files saved to {}".format(dir_path))

    def restore_config_state(self, dir_path):
        """Reload configuration state saved to disk by ModelData.save_config_state()
        """
        if not os.path.exists(dir_path):
            raise IOError("{} does not exist".format(dir_path))

        self.normalised_training_data_df = pd.read_csv(os.path.join(
            os.path.join(dir_path, 'normalised_training_data.csv')))
        self.normalised_pred_data_df = pd.read_csv(os.path.join(os.path.join(dir_path, 'normalised_training_data.csv')))

        with open(os.path.join(dir_path, 'config.json'), 'r') as config_f:
            self.config = json.load(config_f)

    def __validate_config(self, config):

        config_keys = ["train_start_date",
                       "train_end_date",
                       "pred_start_date",
                       "pred_end_date",

                       "include_satellite",
                       "include_prediction_y",
                       "train_sources",
                       "pred_sources",
                       "train_interest_points",
                       "train_satellite_interest_points",
                       "pred_interest_points",
                       "species",
                       "features",
                       "norm_by",
                       "model_type",
                       'tag'
                       ]

        valid_models = ['svgp', ]

        self.logger.info("Validating config")

        # Check required config keys present
        if not set(config_keys).issubset(set(config.keys())):
            missing_keys = [key for key in config_keys if key not in config.keys()]
            raise AttributeError(
                "Config dictionary does not contain correct keys. Must contain {}".format(missing_keys))

        # Check requested features are available
        if config['features'] == 'all':
            features = self.get_available_static_features(output_type='list'
                                                          ) + self.list_available_dynamic_features(config['train_start_date'], config['pred_end_date'])
            if not features:
                raise AttributeError("There are no features in the database. Run feature extraction first")
            self.logger.warning(
                "You have selected 'all' features from the database. It is strongly advised that you choose features manually")
        else:
            self.logger.debug("Checking requested features are availble in database")
            self.__check_features_available(config['features'], config['train_start_date'], config['pred_end_date'])

        # Check training sources are available
        train_sources = config['train_sources']
        self.logger.debug("Checking requested sources for training are availble in database")
        self.__check_sources_available(train_sources)

        # Check prediction sources are available
        pred_sources = config['pred_sources']
        self.logger.debug("Checking requested sources for prediction are availble in database")
        self.__check_sources_available(pred_sources)

        # Check model type is valid
        if config['model_type'] not in valid_models:
            raise AttributeError("{} is not a valid model type. Use one of the following: {}"
                                 .format(config['model_type'], valid_models))

        # Check interest points are valid
        train_interest_points = config['train_interest_points']
        if isinstance(train_interest_points, list):
            self.__check_interest_points_available(train_interest_points, train_sources)

        pred_interest_points = config['pred_interest_points']
        if isinstance(pred_interest_points, list):
            self.__check_interest_points_available(pred_interest_points, pred_sources)

        if config['include_satellite']:
            satellite_interest_points = config['train_satellite_interest_points']
            if isinstance(satellite_interest_points, list):
                self.__check_interest_points_available(pred_interest_points, ['satellite'])

        self.logger.info("Validate config complete")

    def __generate_full_config(self, config):
        """Generate a full config file by querying the cleanair database to check available interest point sources and features"""

        if config['train_interest_points'] == 'all':
            config['train_interest_points'] = self.__get_interest_point_ids(config['train_sources'])
        if config['pred_interest_points'] == 'all':
            config['pred_interest_points'] = self.__get_interest_point_ids(config['pred_sources'])
        if config['include_satellite'] and (config['train_satellite_interest_points'] == 'all'):
            config['train_satellite_interest_points'] = self.__get_interest_point_ids(['satellite'])
        else:
            config['train_satellite_interest_points'] = []

        if config['features'] == 'all':
            feature_names = self.get_available_static_features(output_type='list'
                                                               ) + self.list_available_dynamic_features(config['train_start_date'], config['pred_end_date'])
            buff_size = [1000, 500, 200, 100, 10]
            config['features'] = ["value_{}_{}".format(buff, name) for buff in buff_size for name in feature_names]
            self.logger.info("Features 'all' replaced with available features: %s", config['features'])
            config['feature_names'] = feature_names
        else:
            config['feature_names'] = list(set(["".join(feature.split("_", 2)[2:]) for feature in config['features']]))
        config['x_names'] = ["epoch", "lat", "lon"] + config['features']

        return config

    @property
    def x_names_norm(self):
        """Get the normalised x names"""
        return [x + '_norm' for x in self.config['x_names']]

    @property
    def norm_stats(self):
        """Get the mean and sd used for data normalisation"""

        norm_mean = self.training_data_df[self.training_data_df['source']
                                          == self.config['norm_by']][self.config['x_names']].mean(axis=0)

        norm_std = self.training_data_df[self.training_data_df['source']
                                         == self.config['norm_by']][self.config['x_names']].std(axis=0)

        # Check for zero variance
        if norm_std.eq(0).any().any():
            self.logger.warning("No variance in feature: %s. Setting variance to 1.", norm_std[norm_std == 0].index)
            norm_std[norm_std == 0] = 1

        return norm_mean, norm_std

    def __normalise_data(self, data_df):
        """Normalise the x columns"""
        norm_mean, norm_std = self.norm_stats

        # Normalise the data
        data_df[self.x_names_norm] = ((data_df[self.config['x_names']] - norm_mean) / norm_std)
        
        return data_df

    def __get_model_data_arrays(self, data_df, return_y, dropna=True):
        """Return a dictionary of data arrays for model fitting.
        The returned dictionary includes and index to allow model predictions
        to be appended to dataframes (required when dropna is used)"""

        if return_y:
            data_subset = data_df[self.x_names_norm + self.config['species']]
        else:
            data_subset = data_df[self.x_names_norm]

        if dropna:
            data_subset = data_subset.dropna()  # Must have complete dataset
            n_dropped_rows = data_df.shape[0] - data_subset.shape[0]
            self.logger.warning("Dropped %s rows out of %s from the dataframe", n_dropped_rows, data_df.shape[0])

        data_dict = {'X': data_subset[self.x_names_norm].to_numpy(), 'index': data_subset[self.x_names_norm].index}

        if return_y:
            data_dict['Y'] = data_subset[self.config['species']].to_numpy()

        if self.config['include_satellite']:
            # Check dimensions
            N_sat_box = self.training_satellite_data_x['box_id'].unique().size
            N_hours = self.training_satellite_data_x['epoch'].unique().size
            N_interest_points = self.training_satellite_data_x['point_id'].unique().size
            N_x_names = len(self.config['x_names'])

            X_sat = self.training_satellite_data_x[self.config['x_names']
                                                   ].to_numpy().reshape((N_sat_box * N_hours, 100, N_x_names))

            Y_sat = self.training_satellite_data_y['value'].to_numpy()
            data_dict['X_sat'] = X_sat
            data_dict['Y_sat'] = Y_sat

        return data_dict

    def get_training_data_arrays(self, dropna=True):
        """The the training data arrays.

        args:
            dropna: Drop any rows which contain NaN
        """
        return self.__get_model_data_arrays(self.normalised_training_data_df, return_y=True, dropna=dropna)

    def get_pred_data_arrays(self, dropna=True):
        """The the pred data arrays.

        args:
            return_y: Return the sensor data if in the database for the prediction dates
            dropna: Drop any rows which contain NaN
        """
        if self.config['include_prediction_y']:
            return self.__get_model_data_arrays(self.normalised_pred_data_df, return_y=True, dropna=dropna)

        return self.__get_model_data_arrays(self.normalised_pred_data_df, return_y=False, dropna=dropna)

    def __check_features_available(self, features, start_date, end_date):
        """Check that all requested features exist in the database"""

        available_features = self.get_available_static_features(output_type='list'
                                                                ) + self.list_available_dynamic_features(start_date, end_date)
        unavailable_features = []

        for feature in features:
            feature_name_no_buff = "_".join(feature.split("_")[2:])
            if feature_name_no_buff not in available_features:
                unavailable_features.append(feature)

        if unavailable_features:
            raise AttributeError("The following features are not available the cleanair database: {}"
                                 .format(unavailable_features))

    def __check_sources_available(self, sources):
        """Check that sources are available in the database

        args:
            sources: A list of sources
        """

        available_sources = self.get_available_sources(output_type='list')
        unavailable_sources = []

        for source in sources:
            if source not in available_sources:
                unavailable_sources.append(source)

        if unavailable_sources:
            raise AttributeError("The following sources are not available the cleanair database: {}"
                                 .format(unavailable_sources))

    def __get_interest_point_ids(self, sources):

        return self.get_available_interest_points(sources, output_type='df')['point_id'].astype(str).to_numpy().tolist()

    def __check_interest_points_available(self, interest_points, sources):

        available_interest_points = self.__get_interest_point_ids(sources)
        unavailable_interest_points = []

        for point in interest_points:
            if point not in available_interest_points:
                unavailable_interest_points.append(point)

        if unavailable_interest_points:
            raise AttributeError("The following interest points are not available the cleanair database: {}"
                                 .format(unavailable_interest_points))

    def list_available_dynamic_features(self, start_date, end_date):
        """Return a list of the available dynamic features in the database.
            Only returns features that are available between start_date and end_date 
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(IntersectionValueDynamic.feature_name,
                                            func.min(IntersectionValueDynamic.measurement_start_utc),
                                            func.max(IntersectionValueDynamic.measurement_start_utc)).group_by(IntersectionValueDynamic.feature_name)

            available_features = pd.read_sql(feature_types_q.statement,
                                             feature_types_q.session.bind)  # ['feature_name'].tolist()

            # Check if dynamic features are available between the requested dates. If not they are not returned.

            available_features['is_available'] = (available_features['min_1'] <= start_date) & (
                available_features['max_1'] >= end_date)

            if not available_features['is_available'].all():

                not_available = available_features[available_features['is_available'] == False]['feature_name'].tolist()
                self.logger.warning(
                    "The following dynamic features were not available during the time you requested: %s", not_available)

            available = available_features[available_features['is_available'] == True]['feature_name'].tolist()

            return available

    def __select_features(self, feature_table, features, sources, point_ids, start_date=None, end_date=None):
        """Query features from the database. Returns a pandas dataframe if values returned, else returns None"""

        with self.dbcnxn.open_session() as session:

            feature_query = session.query(feature_table).filter(feature_table.feature_name.in_(features))

            if start_date and end_date:
                feature_query = feature_query.filter(feature_table.measurement_start_utc >= start_date,
                                                     feature_table.measurement_start_utc < end_date)

            interest_point_query = self.get_available_interest_points(sources)

            # Select into into dataframes
            features_df = pd.read_sql(feature_query.statement,
                                      feature_query.session.bind)

            interest_point_df = pd.read_sql(interest_point_query.statement,
                                            interest_point_query.session.bind).set_index('point_id')

            # Check if returned dataframes are empty
            if interest_point_df.empty:
                raise AttributeError(
                    "No interest points were returned from the database. Check requested interest points are valid")

            if features_df.empty:
                return features_df

            def get_val(x):
                if len(x) == 1:
                    return x
                raise ValueError("""Pandas pivot table trying to return an array of values.
                                    Here it must only return a single value""")

            # Reshape features df (make wide)
            if start_date:
                features_df = pd.pivot_table(features_df,
                                             index=['point_id', 'measurement_start_utc'],
                                             columns='feature_name', aggfunc=get_val).reset_index()
                features_df.columns = ['point_id', 'measurement_start_utc'] + ['_'.join(col).strip() for
                                                                               col in features_df.columns.to_numpy()[2:]]
                features_df = features_df.set_index('point_id')
            else:
                features_df = features_df.pivot(index='point_id', columns='feature_name').reset_index()
                features_df.columns = ['point_id'] + ['_'.join(col).strip()
                                                      for col in features_df.columns.to_numpy()[1:]]
                features_df = features_df.set_index('point_id')

            # Set index types to str
            features_df.index = features_df.index.astype(str)
            interest_point_df.index = interest_point_df.index.astype(str)

            # Inner join the MetaPoint and IntersectionValue(Dynamic) data
            df_joined = interest_point_df.join(features_df, how='left')
            return df_joined.reset_index()

    def __select_dynamic_features(self, start_date, end_date, features, sources, point_ids):
        """Read static features from the database.
        """

        return self.__select_features(IntersectionValueDynamic, features, sources, point_ids, start_date, end_date)

    def __select_static_features(self, features, sources, point_ids):
        """Query the database for static features and join with metapoint data

        args:
            source: A list of sources(e.g. 'laqn', 'aqe') to include. Default will include all sources
            point_ids: A list if interest point ids. Default to all ids"""

        return self.__select_features(IntersectionValue, features, sources, point_ids)

    @staticmethod
    def __expand_time(start_date, end_date, feature_df):
        """
        Returns a new dataframe with static features merged with
        hourly timestamps between start_date(inclusive) and end_date
        """
        start_date = isoparse(start_date).date()
        end_date = isoparse(end_date).date()

        ids = feature_df['point_id'].to_numpy()
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date - relativedelta(hours=+1))
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=False)],
                                           names=["point_id", "measurement_start_utc"])
        time_df = pd.DataFrame(index=index).reset_index()
        time_df_merged = time_df.merge(feature_df)
        time_df_merged['epoch'] = time_df_merged['measurement_start_utc'].apply(lambda x: x.timestamp())
        return time_df_merged

    def __get_sensor_readings(self, start_date, end_date, sources, species):
        """Get sensor readings for the sources between the start_date(inclusive) and end_date"""

        self.logger.debug("Getting sensor readings for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                          sources, species, start_date, end_date)

        start_date_ = isoparse(start_date)
        end_date_ = isoparse(end_date)

        sensor_dfs = []
        if 'laqn' in sources:
            laqn_sensor_data = self.get_laqn_readings(start_date_, end_date_, output_type='df')
            sensor_dfs.append(laqn_sensor_data)
            if laqn_sensor_data.shape[0] == 0:
                raise AttributeError(
                    "No laqn sensor data was retrieved from the database. Check data exists for the requested dates")

        if 'aqe' in sources:
            aqe_sensor_data = self.get_aqe_readings(start_date_, end_date_, output_type='df')
            sensor_dfs.append(aqe_sensor_data)
            if aqe_sensor_data.shape[0] == 0:
                raise AttributeError(
                    "No laqn sensor data was retrieved from the database. Check data exists for the requested dates")

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

    def __get_model_features(self, start_date, end_date, features, sources, point_ids):
        """
        Query the database for model features, only getting features in self.features
        """
        static_features = self.__select_static_features(features, sources, point_ids)
        static_features_expand = self.__expand_time(start_date, end_date, static_features)
        dynamic_features = self.__select_dynamic_features(start_date, end_date, features, sources, point_ids)

        if dynamic_features.empty:
            self.logger.warning(
                "No dynamic features were returned from the database. If dynamic features were not requested then ignore.")
            return static_features_expand

        return static_features_expand.merge(dynamic_features, how='left', on=['point_id',
                                                                              'measurement_start_utc',
                                                                              'source',
                                                                              'lon',
                                                                              'lat'])

    def get_training_data_inputs(self):
        """
        Query the database to get inputs for model fitting.
        """

        start_date = self.config['train_start_date']
        end_date = self.config['train_end_date']
        sources = self.config['train_sources']
        species = self.config['species']
        point_ids = self.config['train_interest_points']
        features = self.config['feature_names']

        self.logger.info("Getting training data for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                         sources, species, start_date, end_date)

        # Get sensor readings and summary of availible data from start_date (inclusive) to end_date
        all_features = self.__get_model_features(start_date, end_date, features, sources, point_ids)
        readings = self.__get_sensor_readings(start_date, end_date, sources, species)

        self.logger.debug("Merging sensor data and model features")
        model_data = pd.merge(all_features,
                              readings,
                              on=['point_id', 'measurement_start_utc', 'epoch', 'source'],
                              how='left')

        return model_data

    def get_pred_data_inputs(self):
        """Query the database for inputs for model prediction"""

        start_date = self.config['pred_start_date']
        end_date = self.config['pred_end_date']
        species = self.config['species']
        sources = self.config['pred_sources']
        point_ids = self.config['pred_interest_points']
        features = self.config['feature_names']

        self.logger.info("Getting prediction data for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                         sources, species, start_date, end_date)

        all_features = self.__get_model_features(start_date, end_date, features, sources, point_ids)
        if self.config['include_prediction_y']:
            readings = self.__get_sensor_readings(start_date, end_date, sources, species)
            self.logger.debug("Merging sensor data and model features")
            model_data = pd.merge(all_features,
                                  readings,
                                  on=['point_id', 'measurement_start_utc', 'epoch', 'source'],
                                  how='left')

            return model_data

        return all_features

    def get_training_satellite_inputs(self):
        """Get satellite inputs"""
        start_date = self.config['train_start_date']
        end_date = self.config['train_end_date']
        sources = ['satellite']
        species = self.config['species']
        point_ids = self.config['train_satellite_interest_points']
        features = self.config['feature_names']

        self.logger.info("Getting Satellite training data for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
                         sources, species, start_date, end_date)

        all_features = self.__get_model_features(start_date, end_date, features, sources, point_ids)
        # all_features.to_csv('/secrets/satdata.csv')

        with self.dbcnxn.open_session() as session:

            sat_site_map_q = session.query(SatelliteDiscreteSite)
            sat_q = session.query(SatelliteForecastReading).filter(SatelliteForecastReading.measurement_start_utc >= start_date,
                                                                   SatelliteForecastReading.measurement_start_utc < end_date)
        sat_site_map_df = pd.read_sql(sat_site_map_q.statement, sat_site_map_q.session.bind)

        # Convert uuid to strings to allow merge
        all_features['point_id'] = all_features['point_id'].astype(str)
        sat_site_map_df['point_id'] = sat_site_map_df['point_id'].astype(str)

        # Get satellite box id for each feature interest point
        all_features = all_features.merge(sat_site_map_df, how='left', on=['point_id'])

        # Get satellite data
        satellite_readings = pd.read_sql(sat_q.statement, sat_q.session.bind)
        return all_features, satellite_readings

    def update_model_results_df(self, predict_data_dict, Y_pred, model_fit_info):
        """Update the model results data frame with model predictions"""
        # Create new dataframe with predictions
        predict_df = pd.DataFrame(index=predict_data_dict['index'])
        predict_df['predict_mean'] = Y_pred[:, 0]
        predict_df['predict_var'] = Y_pred[:, 1]
        predict_df['fit_start_time'] = model_fit_info['fit_start_time']
        predict_df['tag'] = self.config['tag']

        # # Concat the predictions with the predict_df
        self.normalised_pred_data_df = pd.concat([self.normalised_pred_data_df, predict_df], axis=1, ignore_index=False)

    def update_remote_tables(self):
        """Update the model results table with the model results"""

        record_cols = ['tag', 'fit_start_time', 'point_id', 'measurement_start_utc', 'predict_mean', 'predict_var']
        df_cols = self.normalised_pred_data_df
        for col in record_cols:
            if col not in df_cols:
                raise AttributeError("""The data frame must contain the following columns: {}.
                                     Ensure model results have been passed to ModelData.update_model_results_df()"""
                                     .format(record_cols))

        upload_records = self.normalised_pred_data_df[record_cols].to_dict('records')

        self.logger.info("Inserting %s records into the database", len(upload_records))
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, upload_records, table=ModelResult)

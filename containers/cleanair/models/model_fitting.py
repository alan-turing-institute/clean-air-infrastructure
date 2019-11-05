from ..databases.tables import IntersectionValue, LAQNSite, LAQNReading, MetaPoint, AQESite, AQEReading
from ..databases.db_interactor import DBInteractor
from sqlalchemy import literal, func
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import rrule

import matplotlib.pyplot as plt
import tensorflow as tf
import gpflow
from scipy.cluster.vq import kmeans2
import time
# import tensorflow as tf

class Logger(gpflow.actions.Action):
    def __init__(self, model):
        self.model = model
        self.logf = []
        
    def run(self, ctx):
        if (ctx.iteration % 10) == 0:
            # Extract likelihood tensor from Tensorflow session
            likelihood = - ctx.session.run(self.model.likelihood_tensor)
            print(likelihood)
            # Append likelihood value to list
            self.logf.append(likelihood)

def run_adam(model, iterations):
    """
    Utility function running the Adam Optimiser interleaved with a `Logger` action.
    
    :param model: GPflow model
    :param interations: number of iterations
    """
    # Create an Adam Optimiser action
    adam = gpflow.train.AdamOptimizer().make_optimize_action(model)
    # Create a Logger action
    logger = Logger(model)
    actions = [adam, logger]
    # Create optimisation loop that interleaves Adam with Logger
    loop = gpflow.actions.Loop(actions, stop=iterations)()
    # Bind current TF session to model
    model.anchor(model.enquire_session())
    return logger

class ModelFitting(DBInteractor):

    def __init__(self, **kwargs):

        # Initialise parent classes
        super().__init__(**kwargs)

    def select_static_features(self, sources=['laqn', 'aqe']):
        """Select static features and join with metapoint data"""

        with self.dbcnxn.open_session() as session:

            feature_query = session.query(IntersectionValue)
            interest_point_query = session.query(MetaPoint.id.label('point_id'),
                                                 MetaPoint.source,
                                                 MetaPoint.location,
                                                 func.ST_X(MetaPoint.location).label('lon'),
                                                 func.ST_Y(MetaPoint.location).label('lat')).filter(MetaPoint.source.in_(sources))

            # Select into into dataframes
            features_df = pd.read_sql(feature_query.statement, 
                                         feature_query.session.bind)

            interest_point_df = pd.read_sql(interest_point_query.statement, 
                                 interest_point_query.session.bind).set_index('point_id')

            # Reshape features df (make wide)
            features_df = features_df.pivot(index = 'point_id', columns = 'feature_name').reset_index()
            features_df.columns = ['point_id'] + ['_'.join(col).strip() for col in features_df.columns.values[1:]]
            features_df = features_df.set_index('point_id')
    
            # Set index types to str
            features_df.index = features_df.index.astype(str)
            interest_point_df.index = interest_point_df.index.astype(str)

            # Inner join the MetaPoint and IntersectionValue data
            df_joined = pd.concat([interest_point_df, features_df], axis=1, sort=False, join  = 'inner')

            return df_joined.reset_index()

    @staticmethod
    def expand_static_feature_df(start_date, end_date, feature_df):
        """
        Returns a new dataframe with static features merged with hourly timestamps between start_date and end_date
        """
        start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

        ids = feature_df['point_id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date)
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=False)], names=["point_id", "measurement_start_utc"])
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
            query = query.filter(LAQNReading.measurement_start_utc.between(start_date, end_date))
            return query

    def __get_aqe_readings(self, start_date, end_date):
        
        with self.dbcnxn.open_session() as session:
            query = session.query(AQEReading.measurement_start_utc, 
                                  AQEReading.species_code, 
                                  AQEReading.value,
                                  AQESite.point_id,
                                  literal('aqe').label('source')).join(AQESite)
            query = query.filter(AQEReading.measurement_start_utc.between(start_date, end_date))
            return query


    def get_sensor_readings(self, start_date, end_date, sources = ['laqn', 'aqe']):
        """Get sensor readings for the sources between the start_date and end_date"""
        
        sensor_dfs = []
        if 'laqn' in sources:
            sensor_q = self.__get_laqn_readings(start_date, end_date)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        if 'aqe' in sources:
            sensor_q = self.__get_aqe_readings(start_date, end_date)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        df = pd.concat(sensor_dfs, axis = 0)
        df['epoch'] = df['measurement_start_utc'].apply(lambda x: x.timestamp())
        df = df.pivot_table(index = ['point_id', 'source', 'measurement_start_utc', 'epoch'], columns = ['species_code'], values = 'value')

        return df.reset_index()

    def get_model_fit_input(self, start_date, end_date, sources=['laqn', 'aqe']):
        """Return the inputs for model fitting between two dates"""

        static_features = self.select_static_features(sources=sources)
        static_features = self.expand_static_feature_df(start_date, end_date, static_features)
        readings = self.get_sensor_readings(start_date, end_date, sources=sources)
        return pd.merge(static_features, 
                        readings, 
                        on=['point_id', 'measurement_start_utc', 'epoch', 'source'], 
                        how='left')


    def prep(self, data_df):

        x=["epoch", "lat", "lon"]
        y=["NO2"]

        data_subset = data_df[x + y]
        data_subset = data_subset.dropna()

        return data_subset[x].values, data_subset[y].values

    
    def model_fit(self):

        fit_data_raw = self.get_model_fit_input(start_date='2019-11-02', end_date='2019-11-03', sources=['laqn'])
        fit_data_raw.to_csv('/secrets/model_data.csv')
        
        X, Y = self.prep(fit_data_raw)

        X_norm = (X - X.mean()) / X.std()
        Y_norm = Y.copy()

        # X_norm = X.copy()
        # Y_norm = Y.copy()
        print(X_norm.shape, Y_norm.shape)
        num_z = X_norm.shape[0]

        i = 0
        Z = kmeans2(X_norm, num_z, minit='points')[0] 
        # print(Z)
        kern = gpflow.kernels.RBF(X_norm.shape[1], lengthscales=0.1)
        # Z = X_norm.copy()
        m = gpflow.models.SVGP(X_norm, Y_norm, kern, gpflow.likelihoods.Gaussian(variance=0.1), Z, minibatch_size=500)
    
        # m.compile()

        logger = run_adam(m, 5000)
        
        print(-np.array(logger.logf))
        # opt = gpflow.train.AdamOptimizer()
        # print('fitting')
        # opt.minimize(m)
        print('predict')
        ys_total = []
        # for i in range(len(X)):
        ys, ys_var = m.predict_y(X_norm)
        ys_total.append([ys, ys_var])
        ys_total = np.array(ys_total)


        # np.save('/secrets/_ys', ys_total)
        # np.save('/secrets/true_ys', Y_norm)

        

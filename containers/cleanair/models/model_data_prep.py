from ..databases.tables import IntersectionValue, LAQNSite, LAQNReading, MetaPoint, AQESite, AQEReading
from ..databases.db_interactor import DBInteractor
from sqlalchemy import literal, func, String
from sqlalchemy.dialects.postgresql import ARRAY
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
import plotly.figure_factory as ff


class ModelData(DBInteractor):
    """Class to query sensor readings and features from the cleanair database and format for model fitting"""

    def __init__(self, **kwargs):
        # Initialise parent classes

        super().__init__(**kwargs)

    def __get_interest_points(self, source='laqn'):
        """Get all interest points for a given source"""    

        with self.dbcnxn.open_session() as session:

            interest_point_query = session.query(MetaPoint.id.label('point_id'),
                                                 MetaPoint.source,
                                                 MetaPoint.location,
                                                 func.ST_X(MetaPoint.location).label('lon'),
                                                 func.ST_Y(MetaPoint.location).label('lat')).filter(MetaPoint.source == source)

            return interest_point_query

    
    def viz_sensor_data(self, start_date, end_date, source='laqn', species='NO2'):
        """Launch a plotly webapp to see missing data"""

        start_date_ = isoparse(start_date)
        end_date_ = isoparse(end_date)        
       
        interest_point_q = self.__get_interest_points(source=source)
        interest_point_sq = interest_point_q.subquery()

        if source == 'laqn':
            INFOSite = LAQNSite
        elif source == 'aqe':
            INFOSite = AQESite

        with self.dbcnxn.open_session() as session:

            interest_points_join_INFOSite_q = session.query(interest_point_sq,
                                                     INFOSite.site_code,                                                     
                                                     INFOSite.date_opened,
                                                     INFOSite.date_closed).join(INFOSite, isouter=True)

            interest_point_join_df = pd.read_sql(interest_points_join_INFOSite_q.statement, 
                                            interest_points_join_INFOSite_q.session.bind)           

            interest_point_join_df['point_id'] = interest_point_join_df['point_id'].astype(str)
            interest_point_df = interest_point_join_df.groupby(['point_id', 
                                                                'source',
                                                                'lon',
                                                                'lat']).agg({'date_opened': 'min',
                                                                             'date_closed': 'max'}).reset_index()          
            
            ids = interest_point_df['point_id'].values
            times = rrule.rrule(rrule.HOURLY, dtstart=start_date_, until=end_date_-relativedelta(hours=+1))     
            index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=False)], names=["point_id", "measurement_start_utc"])            
            time_df = pd.DataFrame(index=index).reset_index()
            time_df_merged = time_df.merge(interest_point_df)
            
            # Check if an interest_point was open at all times
            time_df_merged['open'] = (
                                      (time_df_merged['date_opened'] <= time_df_merged['measurement_start_utc']) & 
                                      ((time_df_merged['measurement_start_utc'] < time_df_merged['date_closed']) | pd.isnull(time_df_merged['date_closed']))
                                     )           

            # Prep the gant chart
            sensor_readings = self.get_sensor_readings(start_date, end_date, sources = [source])                     
            time_df_merged = pd.merge(time_df_merged, sensor_readings, how = 'left', on=['point_id', 'measurement_start_utc','source'])
            time_df_merged['missing_reading'] = pd.isnull(time_df_merged[species])

            def categorise(x):

                if not x['open']:
                    return 'Closed'
                elif x['open'] and not x['missing_reading']:
                    return 'OK'
                else:
                    return 'Missing'
                
       
            time_df_merged['Resource'] = time_df_merged.apply(lambda x: categorise(x), axis=1)

            gant_df = time_df_merged[['point_id', 'measurement_start_utc', 'Resource']].rename(columns={'point_id': 'Task', 'measurement_start_utc': 'Start'})
            gant_df['Finish'] = gant_df['Start'] + pd.DateOffset(hours=1)

            gant_df['Start'] = gant_df['Start'].apply(lambda x: datetime.strftime(x,  '%Y-%m-%d %H:%M:%S'))
            gant_df['Finish'] = gant_df['Finish'].apply(lambda x: datetime.strftime(x,  '%Y-%m-%d %H:%M:%S'))


            # gant_df = gant_df.groupby(['Task', 'Resource']).agg({'Start': 'min', 'Finish': 'max'}).reset_index() #This does the wrong thing. But something similar required to do something similar

            # Create the gant chart
            colors = dict(OK = '#72C14D',
                          Missing = '#D80032',
                          Closed = '#1E1014',)
     
            fig = ff.create_gantt(gant_df, group_tasks=True, colors=colors, index_col='Resource', show_colorbar=True, showgrid_x=True)
            fig['layout'].update(autosize=True, height = 7000, title = "Dataset: {}".format(source))
            fig.show()

    def select_static_features(self, sources=['laqn', 'aqe'], point_ids=None):
        """Select static features and join with metapoint data"""

        with self.dbcnxn.open_session() as session:

            feature_query = session.query(IntersectionValue)
            interest_point_query = session.query(MetaPoint.id.label('point_id'),
                                                 MetaPoint.source,
                                                 MetaPoint.location,
                                                 func.ST_X(MetaPoint.location).label('lon'),
                                                 func.ST_Y(MetaPoint.location).label('lat')).filter(MetaPoint.source.in_(sources))
            
            if point_ids is not None:
                interest_point_query = interest_point_query.filter(MetaPoint.id.in_(point_ids))

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
        start_date = isoparse(start_date).date()
        end_date = isoparse(end_date).date()

        ids = feature_df['point_id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date-relativedelta(hours=+1))
        print(min(times), max(times))
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


    def get_sensor_readings(self, start_date, end_date, sources = ['laqn'], species = ['NO2']):
        """Get sensor readings for the sources between the start_date and end_date"""

        start_date_ = isoparse(start_date)
        end_date_ = isoparse(end_date)

        sensor_dfs = []
        if 'laqn' in sources:
            sensor_q = self.__get_laqn_readings(start_date_, end_date_)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        if 'aqe' in sources:
            sensor_q = self.__get_aqe_readings(start_date_, end_date_)
            sensor_dfs.append(pd.read_sql(sensor_q.statement, sensor_q.session.bind))

        df = pd.concat(sensor_dfs, axis = 0)
        df['point_id'] = df['point_id'].astype(str)
        df['epoch'] = df['measurement_start_utc'].apply(lambda x: x.timestamp())
        df = df.pivot_table(index = ['point_id', 'source', 'measurement_start_utc', 'epoch'], columns = ['species_code'], values = 'value')        

        return df[species].reset_index() 
    
    def get_model_inputs(self, start_date, end_date, sources=['laqn'], species=['NO2']):
        """
        Query the database for model inputs. Returns all features.
        """
                     
        # Get sensor readings and summary of availible data from start_date (inclusive) to end_date
        readings = sensor_readings = self.get_sensor_readings(start_date, end_date, sources=sources, species=species)            
        static_features = self.select_static_features(sources=sources)
        static_features_expand = self.expand_static_feature_df(start_date, end_date, static_features)        
        model_data = pd.merge(static_features_expand, 
                        readings, 
                        on=['point_id', 'measurement_start_utc', 'epoch', 'source'], 
                        how='left')

        return model_data


    #     # fit_data_raw = self.get_model_fit_input(start_date='2019-11-02', end_date='2019-11-03', sources=['laqn'])
    #     # fit_data_raw.to_csv('/secrets/model_data.csv')
    #     ids = model_data['point_id'].unique()[:20]
    #     # model_data = model_data[model_data['point_id'].apply(lambda x: x in ids)]

    #     X, Y = self.prep(model_data)

    # #     X = np.expand_dims(X, 0)
    # #     Y = np.expand_dims(Y, 0)

    # #     np.save('/secrets/X.npy', X)
    # #     np.save('/secrets/Y.npy', Y)
    # #     print(X)
    # #     print(Y)
    # #     print(Y.shape)

    # #     X = X[0]
    # #     Y = Y[0]

      
    #     X_norm = ((X - X.mean(0)) / X.std(0)).copy()
    #     Y_norm = Y.copy()

        
    #     print(X_norm.shape, Y_norm.shape)
    #     num_z = 1000

    #     i = 0
    #     Z = kmeans2(X_norm, num_z, minit='points')[0] 
    #     # print(Z)
    #     kern = gpflow.kernels.RBF(X_norm.shape[1], lengthscales=0.1)
    #     # Z = X_norm.copy()
    #     m = gpflow.models.SVGP(X_norm, Y_norm, kern, gpflow.likelihoods.Gaussian(variance=0.1), Z, minibatch_size=500)
    
    #     # m.compile()

    #     logger = run_adam(m, 30000)
        
    #     # print("loglik: {:20.4f}".format(-np.array(logger.logf))))
    #     # opt = gpflow.train.AdamOptimizer()
    #     # print('fitting')
    #     # opt.minimize(m)
    #     print('predict')
    #     ys_total = []
    #     # for i in range(len(X)):
    #     ys, ys_var = m.predict_y(X_norm)
    #     ys_total.append([ys, ys_var])
    #     ys_total = np.array(ys_total)


    #     np.save('/secrets/_ys', ys_total)
    #     np.save('/secrets/true_ys', Y_norm)

        

from ..databases.tables import IntersectionValue, LAQNSite, LAQNReading, MetaPoint
from ..databases.db_interactor import DBInteractor
import pandas as pd 
from datetime import datetime
from dateutil import rrule
import matplotlib.pyplot as plt 

class ModelFitting(DBInteractor):

    def __init__(self, **kwargs):

        # Initialise parent classes
        super().__init__(**kwargs)
    
    def get_static_features(self):

        with self.dbcnxn.open_session() as session:

            query = session.query(IntersectionValue)

            df = pd.read_sql(query.statement, query.session.bind)
            df = df.pivot(index = 'point_id', columns = 'feature_name').reset_index()    
            df.columns = ['point_id'] + ['_'.join(col).strip() for col in df.columns.values[1:]]      

            return df

    def get_laqn_readings(self, start_date, end_date):

        with self.dbcnxn.open_session() as session:

            query = session.query(LAQNSite.point_id, 
                                  LAQNSite.site_code, MetaPoint.location, 
                                  LAQNReading.measurement_start_utc, 
                                  LAQNReading.species_code, 
                                  LAQNReading.value).join(MetaPoint).join(LAQNReading)

            query = query.filter(LAQNReading.measurement_start_utc.between(start_date, end_date))      

            df = pd.read_sql(query.statement, query.session.bind)
            return df.reset_index()
         

    @staticmethod
    def expand_static_feature_df(start_date, end_date, feature_df):
        """
        Returns a new dataframe with UKMap features merged with hourly timestamps between start_date and end_date
        """
        start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

        ids = feature_df['point_id'].values
        times = rrule.rrule(rrule.HOURLY, dtstart=start_date, until=end_date)
        index = pd.MultiIndex.from_product([ids, pd.to_datetime(list(times), utc=False)], names=["point_id", "measurement_start_utc"])
        time_df = pd.DataFrame(index=index).reset_index()
        time_df_merged = time_df.merge(feature_df)

        return time_df_merged

    def main(self):

 
        start_date, end_date = '2019-10-12', '2019-10-13'

        static_features = self.get_static_features()
        
        static_features = self.expand_static_feature_df(start_date, end_date, static_features)
        print(static_features.columns)
        # static_features.to_csv("/secrets/test.csv")

        laqn_readings = self.get_laqn_readings(start_date, end_date)
        print(laqn_readings.columns)
        laqn_readings.to_csv("/secrets/test.csv")

        # pd.merge(static_features, laqn_readings, on=['point_id', 'measurement_start_utc'], how = 'left').to_csv("/secrets/testmerge.csv")
       
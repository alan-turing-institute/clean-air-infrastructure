"""Traffic model fitting"""
import sys
sys.path.append("/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers")
from datetime import datetime
from scipy.cluster.vq import kmeans2
import numpy as np
from dateutil.parser import isoparse
from cleanair.databases.tables import (ScootRoadReading)
from cleanair.databases import DBReader
from cleanair.loggers import get_logger
import logging
import pandas as pd 
from fbprophet import Prophet

logging.basicConfig()

class TrafficModelData(DBReader):

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def get_road_profiles(self, start_date, end_date):

        start_date = isoparse(start_date)
        end_date = isoparse(end_date)

        with self.dbcnxn.open_session() as session:

            scoot_road_q = session.query(ScootRoadReading).filter(ScootRoadReading.measurement_start_utc >= start_date,
                                                   ScootRoadReading.measurement_start_utc < end_date).order_by(ScootRoadReading.road_toid, ScootRoadReading.measurement_start_utc)


            return pd.read_sql(scoot_road_q.limit(1000).statement, scoot_road_q.session.bind)



traffic = TrafficModelData(secretfile='/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json')

traffic_data = traffic.get_road_profiles('2019-11-10', '2019-12-11')

sub_dat = traffic_data[traffic_data['road_toid'] == 'osgb4000000027865921']

y_name = ['measurement_start_utc', 'occupancy_percentage']

fit_data = sub_dat[y_name].copy()
fit_data = fit_data.rename(columns={'measurement_start_utc': 'ds', y_name[1]: 'y'})

m = Prophet(changepoint_prior_scale=0.01).fit(fit_data)

predict_df = m.make_future_dataframe(0, freq='H', include_history=True)
forecast = m.predict(predict_df)


fig = m.plot(forecast)
"""Traffic model fitting"""
import sys
sys.path.append("/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers")
from datetime import datetime
from scipy.cluster.vq import kmeans2
import numpy as np
from dateutil.parser import isoparse
from cleanair.databases.tables import (ScootRoadReading, ScootDetector, ScootReading)
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

    def list_scoot_detectors(self):
        """List all availabel scoot detectors"""

        with self.dbcnxn.open_session() as session:
            scoot_detector_q = session.query(ScootDetector.detector_n,
                                             ScootDetector.toid,
                                             ScootDetector.date_installed)

        return pd.read_sql(scoot_detector_q.statement, scoot_detector_q.session.bind)


    def get_training_data(self, start_date, end_date, scoot_ids=NotImplemented):
        """Get scoot readings between start_date and end_date

        args:
            start_date: Date to get data from (inclusive)
            end_date: Date to get data to (exclusive)
            scoot_ids: List of ids to get data for

        """
        start_date = isoparse(start_date)
        end_date = isoparse(end_date)

        with self.dbcnxn.open_session() as session:

            scoot_road_q = session.query(ScootReading).filter(ScootReading.measurement_start_utc >= start_date,
                                                              ScootReading.measurement_start_utc < end_date,
                                                              )

            if scoot_ids:
                scoot_road_q = scoot_road_q.filter(ScootReading.detector_id.in_(scoot_ids))

            scoot_road_q = scoot_road_q.order_by(ScootReading.detector_id, ScootReading.measurement_start_utc)

        return pd.read_sql(scoot_road_q.statement, scoot_road_q.session.bind)



traffic = TrafficModelData(secretfile='/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json')

scoot_detectors = traffic.list_scoot_detectors()

sub_data = traffic.get_training_data('2019-11-01', '2019-11-10', [scoot_detectors['detector_n'].values[0]])



y_name = ['measurement_start_utc', 'occupancy_percentage']

fit_data = sub_data[y_name].copy()
fit_data = fit_data.rename(columns={'measurement_start_utc': 'ds', y_name[1]: 'y'})

m = Prophet(changepoint_prior_scale=0.01).fit(fit_data)

predict_df = m.make_future_dataframe(100, freq='H', include_history=True)
forecast = m.predict(predict_df)


fig = m.plot(forecast)
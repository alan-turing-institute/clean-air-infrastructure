"""Traffic model fitting"""
import sys
import logging
import time
from datetime import datetime
from dateutil.parser import isoparse
from fbprophet import Prophet
from multiprocessing import Pool, cpu_count
from scipy.cluster.vq import kmeans2
import numpy as np
import pandas as pd
from cleanair.databases import DBReader
from cleanair.databases.tables import (ScootRoadReading, ScootDetector, ScootReading)
from cleanair.loggers import get_logger, duration, green

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

        self.logger.info("Requesting scoot data between %s and %s", start_date, end_date)
        start_date = isoparse(start_date)
        end_date = isoparse(end_date)

        with self.dbcnxn.open_session() as session:

            scoot_road_q = session.query(ScootReading).filter(ScootReading.measurement_start_utc >= start_date,
                                                              ScootReading.measurement_start_utc < end_date,
                                                              )

            if scoot_ids:
                scoot_road_q = scoot_road_q.order_by(ScootReading.detector_id, ScootReading.measurement_start_utc)
        return pd.read_sql(scoot_road_q.statement, scoot_road_q.session.bind)


def fit_fbprophet_model(data_dict, n_pred_hours=48, y_name = 'occupancy_percentage'):
    """Fit the traffic model"""

    fit_data = data_dict['fit_data']
    detector_n = data_dict['detector_n']

    fit_data = fit_data.rename(columns={'measurement_start_utc': 'ds', y_name: 'y'})
    m = Prophet(changepoint_prior_scale=0.01).fit(fit_data)
    predict_df = m.make_future_dataframe(n_pred_hours, freq='H', include_history=True)
    predict_df['detector_id'] = detector_n
    return predict_df

if __name__ == '__main__':

    logger = get_logger(__name__)
    traffic = TrafficModelData(
        secretfile='/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json')

    # scoot_detectors = traffic.list_scoot_detectors()['detector_n'].tolist()
    scoot_detectors = traffic.list_scoot_detectors()
    sub_data = traffic.get_training_data('2019-11-01', '2019-11-10', scoot_detectors)

    detector_data = [{'detector_n': detector, 'fit_data': sub_data[sub_data['detector_id'] == detector]} for detector in scoot_detectors if (sub_data[sub_data['detector_id'] == detector].shape[0] > 24)]

    logger.info("Fitting scoot models")
    start_time = time.time()
    with Pool(processes=cpu_count()) as pool:
        res = pool.map(fit_fbprophet_model, detector_data)

    all_predictions = pd.concat(res)

    logger.info("Completed scoot model fits after %s seconds", green(duration(start_time, time.time())))

    print(all_predictions)
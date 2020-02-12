"""Traffic model fitting"""
import datetime
from functools import reduce
from fbprophet import Prophet
import logging
import warnings
import pandas as pd
from ..databases import DBReader
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin
from cleanair.databases.tables import ScootDetector, ScootReading

# Turn off fbprophet stdout logger
logging.getLogger('fbprophet').setLevel(logging.ERROR)


class TrafficForecast(DateRangeMixin, DBReader):
    """Traffic forecasting using FB prophet"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.forecast_length_hrs = 48
        self.features = ["n_vehicles_in_interval", "occupancy_percentage", "congestion_percentage", "saturation_percentage"]

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def forecast(self):
        readings = self.scoot_readings(detector_ids=["N08/227b1", "N10/210s1"])
        training_data = dict(tuple(readings.groupby(["detector_id"])))

        # As the most recent reading will not be now but we still want to forecast
        # a fixed distance into the future, we have to calculate how many hours
        # of forecast we need
        last_read_time = max(readings["measurement_start_utc"])
        forecast_end_time = self.end_datetime + datetime.timedelta(hours=self.forecast_length_hrs)
        n_hours_to_predict = int((forecast_end_time - last_read_time).total_seconds() / 3600)

        self.logger.info("Forecasting SCOOT traffic data between %s and %s...", last_read_time, forecast_end_time)

        # Iterate over each detector ID and obtain the forecast for it
        per_detector_forecasts = []
        for detector_id, fit_data in training_data.items():
            per_feature_dfs = [] #[fit_data[["detector_id", "measurement_start_utc", "measurement_end_utc"]]]

            # Iterate over each feature and obtain the forecast for it
            for feature in self.features:
                # Set the maximum value for the fit
                capacity = 100 if "percentage" in feature else 2 * max(fit_data[feature])
                # Construct the prophet model using the fit data
                prophet_data = fit_data.rename(columns={"measurement_start_utc": "ds", feature: "y"})
                prophet_data["cap"] = capacity
                model = Prophet(growth="logistic").fit(prophet_data)
                # Predict over a future time range
                time_range = model.make_future_dataframe(n_hours_to_predict, freq="H")
                time_range["cap"] = capacity
                # forecast = model.predict(time_range)[["ds", "yhat"]].rename(columns={"ds": "measurement_start_utc", "yhat": feature})

                forecast = model.predict(time_range)
                plot = model.plot(forecast)
                plot.savefig("/secrets/{}_{}.png".format(feature, detector_id.replace("/", "-")))


                # Only keep future predictions and force all predictions to be positive
                forecast = forecast[["ds", "yhat"]].rename(columns={"ds": "measurement_start_utc", "yhat": feature})
                forecast = forecast[forecast["measurement_start_utc"] > last_read_time]
                forecast[feature][forecast[feature] < 0] = 0
                per_feature_dfs.append(forecast)
            per_detector_forecasts.append(reduce(lambda df1, df2: df1.merge(df2, on="measurement_start_utc"), per_feature_dfs))

        output = pd.concat(per_detector_forecasts, ignore_index=True)
        print(output)
        return output




        # training_data = [{"detector_n": detector, 'fit_data': sub_data[sub_data['detector_id'] == detector]}

        # for detector in scoot_detectors if (sub_data[sub_data['detector_id'] == detector].shape[0] > 24)]



        # sub_data = traffic.get_training_data('2019-11-01', '2019-11-10', scoot_detectors)
        # detector_data = [{'detector_n': detector, 'fit_data': sub_data[sub_data['detector_id'] == detector]} for detector in scoot_detectors if (sub_data[sub_data['detector_id'] == detector].shape[0] > 24)]

#     logger.info("Fitting scoot models")
#     start_time = time.time()
#     with Pool(processes=cpu_count()) as pool:
#         res = pool.map(fit_fbprophet_model, detector_data)

#     all_predictions = pd.concat(res)

#     logger.info("Completed scoot model fits after %s seconds", green(duration(start_time, time.time())))

#     print(all_predictions)






    def update_remote_tables(self):
        """Update the database with new Scoot traffic forecasts."""
        self.logger.info("Starting %s forecasts update...", green("Scoot"))
        # start_update = time.time()


# def fit_fbprophet_model(data_dict, n_pred_hours=48, y_name = 'occupancy_percentage'):
#     """Fit the traffic model"""

#     fit_data = data_dict['fit_data']
#     detector_n = data_dict['detector_n']

#     fit_data = fit_data.rename(columns={'measurement_start_utc': 'ds', y_name: 'y'})
#     m = Prophet(changepoint_prior_scale=0.01).fit(fit_data)
#     predict_df = m.make_future_dataframe(n_pred_hours, freq='H', include_history=True)
#     predict_df['detector_id'] = detector_n
#     return predict_df

    # @property
    # def all_scoot_detectors(self):
    #     """List all available SCOOT detectors"""
    #     with self.dbcnxn.open_session() as session:
    #         scoot_detector_q = session.query(ScootDetector.detector_n,
    #                                          ScootDetector.toid,
    #                                          ScootDetector.date_installed)
    #     return pd.read_sql(scoot_detector_q.statement, scoot_detector_q.session.bind)


    # @property
    def scoot_readings(self, detector_ids=None):
        """Get SCOOT readings between start and end times"""
        self.logger.info("Requesting SCOOT readings between %s and %s", self.start_datetime, self.end_datetime)

        with self.dbcnxn.open_session() as session:
            scoot_road_q = session.query(ScootReading).filter(ScootReading.measurement_start_utc >= self.start_datetime,
                                                              ScootReading.measurement_start_utc < self.end_datetime)
            if detector_ids:
                scoot_road_q = scoot_road_q.filter(ScootReading.detector_id.in_(detector_ids))
            scoot_road_q = scoot_road_q.order_by(ScootReading.detector_id, ScootReading.measurement_start_utc)
        return pd.read_sql(scoot_road_q.statement, scoot_road_q.session.bind)




# if __name__ == '__main__':

#     logger = get_logger(__name__)
#     traffic = TrafficModelData(
#         secretfile='/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json')

#     # scoot_detectors = traffic.list_scoot_detectors()['detector_n'].tolist()




# # traffic = TrafficModelData(secretfile='/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json')

# # traffic_data = traffic.get_road_profiles('2019-11-10', '2019-12-11')

# # sub_dat = traffic_data[traffic_data['road_toid'] == 'osgb4000000027865921']

# # y_name = ['measurement_start_utc', 'occupancy_percentage']

# # fit_data = sub_dat[y_name].copy()
# # fit_data = fit_data.rename(columns={'measurement_start_utc': 'ds', y_name[1]: 'y'})

# # m = Prophet(changepoint_prior_scale=0.01).fit(fit_data)

# # predict_df = m.make_future_dataframe(0, freq='H', include_history=True)
# # forecast = m.predict(predict_df)


# # fig = m.plot(forecast)

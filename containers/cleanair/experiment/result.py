

class Result():
    """
    A result of a model predictions at a given point in time.
    """

    def __init__(self, fit_id, measurement_start_utc, point_id, pollutant, mean, var):
        self.fit_id = fit_id
        self.measurement_start_utc = measurement_start_utc
        self.point_id = point_id
        self.pollutant = pollutant
        self.mean = mean
        self.var = var

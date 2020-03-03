

class Result():
    """
    A result of a model predictions at a given point in time.
    """

    def __init__(self, instance_id, measurement_start_utc, point_id, **kwargs):
        """
        Create a result from a model fit.

        Parameters
        ___

        instance_id : str

        measurement_start_utc : datetime

        point_id : str

        kwargs : dict

        Other Parameters
        ___

        NO2_mean : float

        NO2_var : float

        PM10_mean : float

        PM10_var : float
        """
        if len(kwargs) < 2:
            raise AttributeError("Must pass mean and variance for at least one pollutant.")
        for key, value in kwargs.items():
            if key.find("_mean", len(key)-5, ) == -1 and key.find("_var", len(key)-4, ):
                raise AttributeError(
                    "{k} is not a valid attribute for Result. Should be POLLUTANT_mean or POLLUTANT_var."
                )
            setattr(self, key, value)
        self.instance_id = instance_id
        self.measurement_start_utc = measurement_start_utc
        self.point_id = point_id

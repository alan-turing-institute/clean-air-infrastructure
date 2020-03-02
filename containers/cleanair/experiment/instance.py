import git
from ..models import ModelData

class Instance():
    """
    An instance is one model trained and fitted on some data.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": True,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "model_type": "svgp",
        "tag": "production",
    }

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        default_attrs = dict(
            tag="production",
            cluster_id="azure",
            hash=git.Repo(search_parent_directories=True).head.object.hexsha,
        )
        for key, value in default_attrs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        if not hasattr(self, "model_data"):
            data_config = self.__class__.DEFAULT_DATA_CONFIG
            data_config["tag"] = self.tag
            self.model_data = ModelData(data_config=data_config)

        
        self.instance_id = self.get_instance_id()

    def get_instance_id(self):
        hash_string = self.model_name + str(self.param_id) + self.tag
        hash_string += str(self.data_id) + str(self.cluster_id)
        return hash(hash_string)
        

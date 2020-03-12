"""
Parsers for validation that must read model fit data.
"""

from .base_parser import CleanAirParser
from ..experiment import ValidationInstance


class ValidationParser(CleanAirParser):
    """
    A parser for validation.
    """

    EXPERIMENT_ARGS = CleanAirParser.EXPERIMENT_ARGS + ["predict_read_local", "local_write", "no_db_write", "predict_write", "model_dir", "results_dir", "restore", "save_model_state"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_defaults(
            model_name=ValidationInstance.DEFAULT_MODEL_NAME,
            tag="validation",
            include_prediction_y=True,  # compare pred vs actual
        )
        self.add_argument(
            "-predict_read_local",
            action="store_true",
            help="Read predictions from a local file.",
        )
        # model arguments
        self.add_argument(
            "-restore",
            action="store_true",
            help="Restore the model from model_dir.",
        )
        self.add_argument(
            "-save_model_state",
            action="store_true",
            help="Save the model.",
        )
        self.add_argument(
            "-local_write",
            action="store_true",
            help="Write training/test data to config_dir.",
        )
        self.add_argument(
            "-no_db_write",
            action="store_true",
            help="Do not write result to database.",
        )
        self.add_argument(
            "-predict_write",
            action="store_true",
            help="Write a prediction to the results_dir.",
        )
        self.add_argument(
            "-model_dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory where the model is (re-)stored.",
        )
        self.add_argument(
            "-r",
            "--results_dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory of results.",
        )

    def parse_all(self):
        kwargs, data_args, xp_config, model_args = super().parse_all()
        if xp_config["results_dir"] == "CONFIG_DIR":
            xp_config["results_dir"] = xp_config["config_dir"]
        if xp_config["model_dir"] == "CONFIG_DIR":
            xp_config["model_dir"] = xp_config["config_dir"]
        model_args["model_state_fp"] = xp_config["model_dir"]
        return kwargs, data_args, xp_config, model_args

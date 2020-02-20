"""
The model fitting parser.
"""

from .base_parser import CleanAirParser


class ModelFitParser(CleanAirParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):
        """
        Should be able to:
            - read training/test data from DB (default)
            - read training/test data from directory
            - write training/test data to directory
            - write result to DB (default)
            - turn off writing to DB (overwrite default)
            - write results to file
        """
        super().__init__(**kwargs)
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

    def parse_kwargs(self):
        kwargs = super().parse_kwargs()
        if kwargs["model_dir"] == "CONFIG_DIR":
            kwargs["model_dir"] = kwargs["model_dir"]
        return kwargs

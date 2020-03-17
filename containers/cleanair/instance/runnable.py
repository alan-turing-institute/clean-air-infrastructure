"""
An instance that can be executed using the run() method.
"""

import logging
import json
from datetime import datetime
import pandas as pd
from .instance import Instance
from ..models import ModelData
from ..databases.tables import ModelTable, DataConfig, InstanceTable, ResultTable
from ..mixins import DBQueryMixin
from ..databases import DBReader
from ..timestamps import as_datetime


class RunnableInstance(Instance):
    """
    A runnable instance loads data, fits a model, predicts, then saves the results.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": False,
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
        "tag": "test",
    }

    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,    
        "maxiter": 100,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    DEFAULT_EXPERIMENT_CONFIG = dict(
        secretfile="../../terraform/.secrets/db_secrets.json",
        config_dir="./",
    )

    DEFAULT_MODEL_PARAMS = dict(
        save_model_state=False,
    )

    DEFAULT_MODEL_NAME = "svgp"
   
    def __init__(self, **kwargs):
        """
        A runnable instance is determined by its data, model and experiment settings.

        Parameters
        ___

        data_config : dict, optional
            Settings for data.

        experiment_config : dict, optional
            Settings that do not affect the model outcome, e.g. filepaths.

        model_params : dict, optional
            The parameters to run the model with.

        Other Parameters
        ___

        kwargs : dict, optional
            See `Instance`.
        """
        model_name = kwargs.pop("model_name", self.__class__.DEFAULT_MODEL_NAME)

        # these three dict define an instance
        xp_config = kwargs.get("experiment_config", {})
        model_params = kwargs.get("model_params", {})
        data_config = kwargs.get("data_config", {})

        # get experiment config (filepaths, write/read locally or DB, etc.)
        self.experiment_config = self.__class__.DEFAULT_EXPERIMENT_CONFIG.copy()
        self.experiment_config.update(xp_config)

        logging.debug("Experiment config: %s", json.dumps(self.experiment_config, indent=4))

        super().__init__(
            model_name=model_name,
            secretfile=self.experiment_config["secretfile"],
            **kwargs
        )

        # check if model params has been passed
        if model_params:
            self._model_params = model_params
            self.param_id = RunnableInstance.__hash_dict(model_params)
        elif kwargs.get("param_id"):
            raise NotImplementedError("Cannot yet load parameters from DB.")
        else:
            self._model_params = self.__class__.DEFAULT_MODEL_PARAMS.copy()
            self.param_id = self.__hash_dict(self._model_params)
        
        # get data config dict
        if kwargs.get("data_id"):     # check if data id has been passed
            raise NotImplementedError("Cannot yet read data id from DB.")
        else:
            self._data_config = self.__class__.DEFAULT_DATA_CONFIG.copy()
            self._data_config.update(data_config)
            self._data_config = self.convert_str_to_dates()
            self.data_id = RunnableInstance.__hash_dict(self.convert_dates_to_str())
        
        # make model and data
        self.model = None
        self.model_data = None
        logging.info("Tag is %s", self.tag)
        logging.info("Model name is %s", self.model_name)
        logging.info("Param id is %s", self.param_id)
        logging.info("Data id is %s", self.data_id)
        logging.info("Instance id is %s", self.instance_id)
        logging.info("Cluster id is %s", self.cluster_id)

    @property
    def model_params(self):
        return self._model_params

    @model_params.setter
    def model_params(self, value):
        self._model_params = value
        # update param id
        self.param_id = RunnableInstance.__hash_dict(value)

    @property
    def data_config(self):
        return self._data_config
    
    @data_config.setter
    def data_config(self, value):
        self._data_config = value
        self._data_config = self.convert_str_to_dates()
        self.data_id = RunnableInstance.__hash_dict(self.convert_dates_to_str())

    @staticmethod
    def __hash_dict(value):
        hash_string = json.dumps(value)
        return Instance.hash_fn(hash_string)

    def convert_dates_to_str(self, datetime_format="%Y-%m-%dT%H:%M:%S"):
        return dict(
            self.data_config,
            train_start_date=self.data_config["train_start_date"].strftime(datetime_format),
            train_end_date=self.data_config["train_end_date"].strftime(datetime_format),
            pred_start_date=self.data_config["pred_start_date"].strftime(datetime_format),
            pred_end_date=self.data_config["pred_end_date"].strftime(datetime_format),
        )

    def convert_str_to_dates(self):
        return dict(
            self._data_config,
            train_start_date=as_datetime(self._data_config["train_start_date"]),
            train_end_date=as_datetime(self._data_config["train_end_date"]),
            pred_start_date=as_datetime(self._data_config["pred_start_date"]),
            pred_end_date=as_datetime(self._data_config["pred_end_date"]),
        )

    def load_model_params(self, **kwargs):
        """
        Load model parameters from DB or use defaults.
        """

    def setup_model(self):
        """
        From the model name and params, set up a model.
        """
        logging.info("Setting up model.")
        self.model = self.__class__.MODELS[self.model_name](
            experiment_config=self.experiment_config,
            model_params=self.model_params,
            tasks=self.data_config["species"],
        )

    def update_model_table(self):
        """Upload params to the model table."""
        # save model to database
        records = [dict(
            model_name=self.model_name,
            param_id=self.param_id,
            model_param=self.model_params,
        )]
        logging.info("Inserting 1 row into the model table.")
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, records, table=ModelTable, on_conflict="ignore")

    def load_data(self):
        """
        From the data and experiment config, setup a model data object.
        """
        logging.info("Loading input data from database.")
        self.model_data = ModelData(
            config=self.data_config.copy(), # really important to copy
            secretfile=self.experiment_config["secretfile"],
        )

    def update_data_config_table(self):
        """Upload the data configuration to the DB."""
        logging.info("Inserting 1 row into data config table.")
        records = [dict(
            data_id=self.data_id,
            data_config=self.convert_dates_to_str(),
        )]
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, records, table=DataConfig, on_conflict="ignore")

    def run_model_fitting(self):
        """
        Train the model on data.
        """
        training_data_dict = self.model_data.get_training_data_arrays(dropna=False)
        x_train = training_data_dict["X"]
        y_train = training_data_dict["Y"]

        self.fit_start_time = datetime.now()
        logging.info("Training started.")
        self.model.fit(x_train, y_train)
        logging.info("Training ended.")

    def run_prediction(self):
        """
        Predict on the test set using a trained model.
        """
        logging.info("Prediction started.")
        predict_data_dict = self.model_data.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]
        y_pred = self.model.predict(x_test)
        logging.info("Prediction finished.")
        return y_pred

    def update_results(self, y_pred):
        """
        Update the model data object with results.
        """
        self.model_data.update_test_df_with_preds(y_pred, self.fit_start_time)

    def save_results(self):
        """
        Upload instance, params and results to the database.
        """
        logging.info("Writing predictions to the database.")

        # add results to the results table
        self.model_data.update_remote_tables(self.instance_id)

    def load_results(self):
        """
        Load results from the results table that match the instance id.
        """
        with self.dbcnxn.open_session() as session:
            # get all rows that match the instance id
            results_query = session.query(ResultTable).filter(
                ResultTable.instance_id == self.instance_id
            )
            results_df = pd.read_sql(results_query.statement, results_query.session.bind)
        logging.info("Loaded %s rows from the results table.", len(results_df))
        return results_df


    def run(self):
        """
        Setup, train, predict and update all in one step.
        """
        self.setup_model()
        if hasattr(self, "dbcnxn") and self.tag != "production":
            self.update_model_table()
        else:
            logging.warning("Not writing to model table.")

        self.load_data()
        if hasattr(self, "dbcnxn") and self.tag != "production":
            self.update_data_config_table()
        else:
            logging.warning("Not writing to data config table.")

        self.run_model_fitting()

        if hasattr(self, "dbcnxn") and self.tag != "production":
            self.update_remote_tables()
        else:
            logging.warning("Not writing instance to table.")
        y_pred = self.run_prediction()
        self.update_results(y_pred)
        self.save_results()

    @classmethod
    def instance_from_id(cls, instance_id, experiment_config, **kwargs):
        """
        Given an id, return an initialised runnable instance.
        """
        # instance = cls(
        #     instance_id=instance_id,
        #     experiment_config=experiment_config,
        #     **kwargs,
        # )
        # with instance.dbcnxn.open_session() as session:
        instance_query = InstanceQuery(
            secretfile=experiment_config["secretfile"],
        )
        with instance_query.dbcnxn.open_session() as session:
            # get the row that maches the instance id
            instance_query = session.query(InstanceTable).filter(
                InstanceTable.instance_id == instance_id
            )
            instance_df = pd.read_sql(instance_query.statement, instance_query.session.bind)
            assert len(instance_df) == 1    # exactly one row returned from query
            instance_dict = instance_df.iloc[0].to_dict()

            # load data config using the data id
            logging.info("Load data config from database.")
            data_config_query = session.query(DataConfig).filter(
                DataConfig.data_id == instance_dict["data_id"]
            )
            data_row = data_config_query.one()
            data_config = data_row.data_config

            # laod the model parameters using the param_id and model_name
            logging.info("Load model params from database")
            model_param_query = session.query(ModelTable).filter(
                ModelTable.model_name == instance_dict["model_name"]
            ).filter(
                ModelTable.param_id == instance_dict["param_id"]
            )
            model_row = model_param_query.one()
            model_params = model_row.model_param

        instance = cls(
            instance_id=instance_id,
            experiment_config=experiment_config,
            data_config=data_config,
            model_params=model_params,
            git_hash=instance_dict["git_hash"],
            tag=instance_dict["tag"],
            fit_start_time=instance_dict["fit_start_time"],
            cluster_id=instance_dict["cluster_id"],
            model_name=instance_dict["model_name"],
            **kwargs,
        )
        try:
            assert instance_dict["data_id"] == instance.data_id
        except AssertionError:
            error_message = "Data id and hashed data config do not match. "
            error_message += "Data id from DB is {did} . "
            error_message += "Hashed data config from DB is {hash} . "
            error_message += "Data config is: {conf}"
            error_message = error_message.format(
                did=instance_dict["data_id"],
                hash=instance.data_id,
                conf=json.dumps(instance.convert_dates_to_str(), indent=4),
            )
            raise ValueError(error_message)
        assert instance_dict["param_id"] == instance.param_id
        assert instance == instance.instance_id
        # instance.model_name = instance_dict["model_name"]
        # instance.cluster_id = instance_dict["cluster_id"]
        # instance.tag = instance_dict["tag"]
        # instance.git_hash = instance_dict["git_hash"]
        # instance.fit_start_time = instance_dict["fit_start_time"]

        # return the created instance
        return instance

class InstanceQuery(DBReader):
    """
    A class for querying the instance table and its sister tables.
    """



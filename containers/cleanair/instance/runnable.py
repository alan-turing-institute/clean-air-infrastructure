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
from ..databases import DBReader


class RunnableInstance(Instance):
    """
    A runnable instance loads data, fits a model, predicts, then saves the results.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29 00:00:00",
        "train_end_date": "2020-01-30 00:00:00",
        "pred_start_date": "2020-01-30 00:00:00",
        "pred_end_date": "2020-01-31 00:00:00",
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
            # ToDo: remove info
            logging.info("Model params case 1 in runnable init")
            self._model_params = model_params
            self.param_id = RunnableInstance.__hash_dict(model_params)
        elif kwargs.get("param_id"):
            logging.info("Model params case 2 in runnable init")
            self.param_id = kwargs.get("param_id")
            self.model_params = self.load_model_params()
        else:
            logging.info("Model params case 3 in runnable init")
            self._model_params = self.__class__.DEFAULT_MODEL_PARAMS.copy()
            self.param_id = self.__hash_dict(self._model_params)
        
        # get data config dict
        if kwargs.get("data_id"):     # check if data id has been passed
            self.data_id = kwargs.get("data_id")
            data_id = self.data_id
            self.data_config = self.load_data_config()
            self.data_id = RunnableInstance.__hash_dict(
                ModelData.convert_dates_to_str(self.data_config)
            )
        else:
            self._data_config = self.__class__.DEFAULT_DATA_CONFIG.copy()
            self._data_config.update(data_config)
            self._data_config = ModelData.convert_str_to_dates(self._data_config)
            self.data_id = RunnableInstance.__hash_dict(
                ModelData.convert_dates_to_str(self._data_config)
            )

        # make model and data
        self.model = None
        self.model_data = None

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
        self._data_config = ModelData.convert_str_to_dates(self._data_config)
        self.data_id = RunnableInstance.__hash_dict(
            ModelData.convert_dates_to_str(self._data_config)
        )

    @staticmethod
    def __hash_dict(value):
        # it is ESSENTIAL to sort by keys when creating hashes!
        hash_string = json.dumps(value, sort_keys=True)
        return Instance.hash_fn(hash_string)



    def load_model_params(self, **kwargs):
        """
        Loads the model params from the DB.

        Returns
        ___

        model_params : dict
            Dictionary of model parameters.
        """
        if not hasattr(self, "model_name") and not self.model_name:
            raise AttributeError("model_name attribute must be set to load model params from DB")
        if not hasattr(self, "param_id") and not self.param_id:
            raise AttributeError("param_id attribute must be set to load model_params from DB.")

        with self.dbcnxn.open_session() as session:
            logging.info("Load model params from database")
            model_param_query = session.query(ModelTable).filter(
                ModelTable.model_name == self.model_name
            ).filter(
                ModelTable.param_id == self.param_id
            )
            model_row = model_param_query.one()
            return model_row.model_param

    def setup_model(self):
        """
        From the model name and params, set up a model.
        """
        logging.info("Setting up model.")
        self.model = self.__class__.MODELS[self.model_name](
            experiment_config=self.experiment_config,
            model_params=self.model_params.copy(),
            tasks=self.data_config["species"],
        )

    def save_model_params(self, **kwargs):
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
            config=self.data_config.copy(),
            secretfile=self.experiment_config["secretfile"],
        )
        self.data_config = self.model_data.config    # note this will change data_config

    def load_data_config(self):
        """
        Get the data config from a data id by loading from DB.
        """

        if not hasattr(self, "data_id") or not self.data_id:
            raise AttributeError("Instance must have data_id attribute set.")

        with self.dbcnxn.open_session() as session:
            # load data config using the data id
            logging.info("Load data config from database.")
            data_config_query = session.query(DataConfig).filter(
                DataConfig.data_id == self.data_id
            )
            data_row = data_config_query.one()
            return ModelData.convert_str_to_dates(data_row.data_config)

    def save_data(self):
        """
        Save data to local file (only implemented in ValidationInstance).
        """

    def update_data_config_table(self):
        """Upload the data configuration to the DB."""
        logging.info("Inserting 1 row into data config table.")
        data_config = ModelData.convert_dates_to_str(self.data_config)
        assert isinstance(data_config["pred_interest_points"], list)
        records = [dict(
            data_id=self.data_id,
            data_config=data_config,
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

    def load_results(self, training_set=False, test_set=True):
        """
        Load results from the results table that match the instance id and update model data.
        """
        if training_set:
            raise NotImplementedError("Cannot yet load results for the training set.")
        with self.dbcnxn.open_session() as session:
            # get all rows that match the instance id
            results_query = session.query(ResultTable).filter(
                ResultTable.instance_id == self.instance_id
            )
            results_df = pd.read_sql(results_query.statement, results_query.session.bind)
        logging.info("Loaded %s rows from the results table.", len(results_df))
        if test_set:
            self.model_data.normalised_pred_data_df = pd.merge(
                self.model_data.normalised_pred_data_df,
                results_df,
                how="inner",
                on=["point_id", "measurement_start_utc"],
            )
            return results_df
        logging.warning("No testing set data returned.")
        return pd.DataFrame()


    def run(self):
        """
        Setup, train, predict and update all in one step.
        """
        self.setup_model()
        self.save_model_params(filename="model_params.json")

        self.load_data()
        self.save_data()
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
        logging.info("Tag is %s", self.tag)
        logging.info("Model name is %s", self.model_name)
        logging.info("Param id is %s", self.param_id)
        logging.info("Data id is %s", self.data_id)
        logging.info("Instance id is %s", self.instance_id)
        logging.info("Cluster id is %s", self.cluster_id)

    @classmethod
    def instance_from_id(cls, instance_id, experiment_config, **kwargs):
        """
        Given an id, return an initialised runnable instance.
        """
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

        # create a new instance with all the loaded parameters
        instance = cls(
            experiment_config=experiment_config,
            **instance_dict,
            # **kwargs,
        )
        # check that the data id is the same has the hashed data config
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
                conf=json.dumps(ModelData.convert_dates_to_str(instance.data_config), indent=4),
            )
            raise ValueError(error_message)

        # check the param id is the same as the hashed model_params
        try:
            assert instance_dict["param_id"] == instance.param_id
        except AssertionError:
            error_message = "Param id and hashed model params do not match."
            error_message += " Param id is {pid}"
            error_message += " Hashed model params from DB is {hash}."
            error_message += " Model params are {params}"
            raise ValueError(error_message.format(
                pid=instance_dict["param_id"],
                hash=instance.param_id,
                params=json.dumps(instance.model_params, indent=4),
            ))

        # check the instance id of the Instance object is the same as the original passed instance id
        try:
            assert instance_id == instance.instance_id
        except AssertionError:
            error_message = "Id of created instance and passed instance id do not match."
            raise ValueError(error_message)
        
        # return the created instance
        return instance

class InstanceQuery(DBReader):
    """
    A class for querying the instance table and its sister tables.
    """

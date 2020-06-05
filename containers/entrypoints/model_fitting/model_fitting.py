"""
Model fitting
"""
from datetime import datetime
import os
import pickle
import pandas as pd
from sqlalchemy import inspect
from cleanair.models import ModelData, SVGP, ModelParamSVGP
from cleanair.loggers import initialise_logging
from cleanair.parsers import ModelFitParser
from cleanair.instance import AirQualityInstance, hash_dict

from cleanair.databases import DBWriter
from cleanair.databases.tables import AirQualityResultTable, AirQualityModelTable

class AirQualityResult(DBWriter):
    """The predictions from an air quality model."""

    def __init__(
        self, 
        secretfile: str,
        result_df: pd.DataFrame,
        instance_id: str,
        data_id: str,
        **kwargs
    ):
        super().__init__(secretfile=secretfile, **kwargs)
        self.result_df = result_df
        self.instance_id = instance_id
        self.data_id = data_id
        if "instance_id" not in self.result_df:
            self.result_df["instance_id"] = self.instance_id
        if "data_id" not in self.result_df:
            self.result_df["data_id"] = self.data_id
    
    def update_remote_tables(self):
        """Write air quality results to the database."""
        # get column names of result table
        inst = inspect(AirQualityResultTable)
        record_cols = [c_attr.key for c_attr in inst.mapper.column_attrs]

        # filter dataframe by selecting only columns that will be commited to db
        # then convert to records
        records = self.result_df.loc[:, self.result_df.columns.isin(record_cols)].to_dict("records")

        # commit the records to the air quality results table
        self.commit_records(records, table=AirQualityResultTable, on_conflict="ignore")

class AirQualityModelParams(DBWriter):
    """Parameters of an air quality model."""

    def __init__(
        self,
        secretfile: str,
        model_name: str,
        model_params: ModelParamSVGP,
        **kwargs,
    ):
        super().__init__(secretfile=secretfile, **kwargs)
        self.model_name = model_name
        self.model_params = model_params

    @property
    def param_id(self) -> str:
        """Parameter id of the hashed model params dict."""
        return hash_dict(self.model_params)
    
    def update_remote_tables(self):
        """Write the air quality model parameters to the database."""
        records = [dict(
            model_name=self.model_name,
            model_param=self.model_params,
            param_id=self.param_id,
        )]
        self.commit_records(records, table=AirQualityModelTable, on_conflict="ignore")

def write_predictions_to_file(y_pred, results_dir, filename):
    """Write a prediction dict to pickle."""
    pred_filepath = os.path.join(results_dir, filename)
    with open(pred_filepath, "wb") as handle:
        pickle.dump(y_pred, handle)

# TODO: make this into a nice re-usable function somewhere
def validate_shapes(x_array, y_array):
    """Check the shapes of x and y are correct."""
    assert x_array.shape[0] == y_array.shape[0]
    assert x_array.shape[0] > 0
    assert y_array.shape[0] > 0
    assert y_array.shape[1] == 1  # just one task
    assert x_array.shape[1] >= 3  # at least 3 features


def main():  # pylint: disable=R0914
    """
    Run model fitting
    """
    # Parse and interpret command line arguments
    parser = ModelFitParser(description="Run model fitting")
    kwargs = parser.parse_kwargs()
    secretfile=kwargs.get("secretfile")

    # Extract arguments that should not be passed onwards
    logger = initialise_logging(kwargs.pop("verbose", 0))
    no_db_write = kwargs.pop("no_db_write")
    local_write = kwargs.pop("local_write")
    local_read = kwargs.pop("local_read")
    predict_write = kwargs.pop("predict_write")
    results_dir = kwargs.pop("results_dir")
    model_dir = kwargs.pop("model_dir")
    predict_training = kwargs.pop("predict_training")

    # get the model config from the parser arguments
    data_config = parser.generate_data_config()

    if "aqe" in data_config["train_sources"] + data_config["pred_sources"]:
        raise NotImplementedError("AQE cannot currently be run. Coming soon")

    if data_config["species"] != ["NO2"]:
        raise NotImplementedError(
            "The only pollutant we can model right now is NO2. Coming soon"
        )

    # initialise the model
    model_fitter = SVGP(batch_size=1000)  # big batch size for the grid
    model_fitter.model_params["maxiter"] = 10
    model_fitter.model_params["model_state_fp"] = model_dir

    # Get the model data
    if local_read:
        logger.info("Reading local data")
        model_data = ModelData(**kwargs)
    else:
        print("Reading from database using data config.")
        model_data = ModelData(config=data_config, **kwargs)

    # write model results to file
    if local_write:
        model_data.save_config_state(kwargs["config_dir"])

    # get the training and test dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
    x_train = training_data_dict["X"]
    y_train = training_data_dict["Y"]
    x_test = predict_data_dict["X"]

    # Fit the model
    logger.info(
        "Training the model for %s iterations.", model_fitter.model_params["maxiter"]
    )
    fit_start_time = datetime.now()
    print("Fitting model.")
    validate_shapes(x_train["laqn"], y_train["laqn"]["NO2"])
    # print("X hexgrid test shape:", x_test["hexgrid"].shape)
    model_fitter.fit(x_train, y_train)

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction
    print("Predicting at ", datetime.now().isoformat())
    y_test_pred = model_fitter.predict(x_test)
    if predict_training:
        x_train_pred = x_train.copy()
        if "satellite" in x_train:
            x_train_pred.pop("satellite")
        y_train_pred = model_fitter.predict(x_train_pred)
    
    print("Finished predicting at ", datetime.now().isoformat())

    # Internally update the model results in the ModelData object
    model_data.update_test_df_with_preds(y_test_pred, fit_start_time)

    aq_model_params = AirQualityModelParams(secretfile, "svgp", model_fitter.model_params)
    svgp_instance = AirQualityInstance(
        model_name=aq_model_params.model_name,
        param_id=aq_model_params.param_id,
        data_id=model_data.data_id,
        cluster_id="laptop",
        tag="test",
        fit_start_time=fit_start_time,
        secretfile=secretfile,
    )

    # Write the model results to the database
    if not no_db_write:
        # see issue 103: generalise for multiple pollutants
        model_data.normalised_pred_data_df[
            "predict_mean"
        ] = model_data.normalised_pred_data_df["NO2_mean"]
        model_data.normalised_pred_data_df[
            "predict_var"
        ] = model_data.normalised_pred_data_df["NO2_var"]
        result = AirQualityResult(
            secretfile,
            model_data.normalised_pred_data_df,
            svgp_instance.instance_id,
            svgp_instance.data_id,
        )
        # insert records into database - data & model go first, then instance, then result
        model_data.update_remote_tables()
        aq_model_params.update_remote_tables()
        svgp_instance.update_remote_tables()
        result.update_remote_tables()

    # Write the model results to file
    if predict_write:
        write_predictions_to_file(y_test_pred, results_dir, "test_pred.pickle")
        if predict_training:
            write_predictions_to_file(y_train_pred, results_dir, "train_pred.pickle")


if __name__ == "__main__":
    main()

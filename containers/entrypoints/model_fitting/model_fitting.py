"""
Model fitting
"""
from datetime import datetime
import os
import pickle
import pandas as pd
from sqlalchemy import inspect
from cleanair.models import ModelData, SVGP, ModelParamSVGP
from cleanair.parsers import ModelFittingParser
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
        **kwargs,
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
        records = self.result_df.loc[
            :, self.result_df.columns.isin(record_cols)
        ].to_dict("records")

        # commit the records to the air quality results table
        self.commit_records(records, table=AirQualityResultTable, on_conflict="ignore")


class AirQualityModelParams(DBWriter):
    """Parameters of an air quality model."""

    def __init__(
        self, secretfile: str, model_name: str, model_params: ModelParamSVGP, **kwargs,
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
        records = [
            dict(
                model_name=self.model_name,
                model_param=self.model_params,
                param_id=self.param_id,
            )
        ]
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
    parser = ModelFittingParser(description="Run model fitting")
    args = parser.parse_args()

    # get the data config from the parser arguments
    data_config = ModelFittingParser.generate_data_config(args)
    if data_config["species"] != ["NO2"]:
        raise NotImplementedError(
            "The only pollutant we can model right now is NO2. Coming soon"
        )
    # initialise the model
    model_fitter = SVGP(batch_size=1000)  # big batch size for the grid
    model_fitter.model_params["maxiter"] = args.maxiter

    # read data from db
    print("Reading from database using data config.")
    model_data = ModelData(config=data_config, secretfile=args.secretfile)

    # get the training dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    x_train = training_data_dict["X"]
    y_train = training_data_dict["Y"]

    fit_start_time = datetime.now()
    print(
        "Fitting model. Training for {m} iterations".format(
            m=args.maxiter
        )
    )
    print("Start training at", fit_start_time.isoformat())
    validate_shapes(x_train["laqn"], y_train["laqn"]["NO2"])
    model_fitter.fit(x_train, y_train)
    print("Training completed at", datetime.now().isoformat())

    # TODO predict at both the training and test set!
    # predict either at the training or test set
    if args.predict_training:
        x_test = x_train.copy()
    else:
        predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]

    # Do prediction
    print("Predicting at ", datetime.now().isoformat())
    y_pred = model_fitter.predict(x_test)
    print("Finished predicting at ", datetime.now().isoformat())

    # Internally update the model results in the ModelData object
    if args.predict_training:
        model_data.update_training_df_with_preds(y_pred, fit_start_time)
        result_df = model_data.normalised_training_data_df
    else:
        model_data.update_test_df_with_preds(y_pred, fit_start_time)
        result_df = model_data.normalised_pred_data_df

    aq_model_params = AirQualityModelParams(
        args.secretfile, "svgp", model_fitter.model_params
    )
    svgp_instance = AirQualityInstance(
        model_name=aq_model_params.model_name,
        param_id=aq_model_params.param_id,
        data_id=model_data.data_id,
        cluster_id="laptop",
        tag=args.tag,
        fit_start_time=fit_start_time,
        secretfile=args.secretfile,
    )

    # Write the model results to the database
    # see issue 103: generalise for multiple pollutants
    # result_df["predict_mean"] = result_df["NO2_mean"]
    # result_df["predict_var"] = result_df["NO2_var"]
    result = AirQualityResult(
        args.secretfile, result_df, svgp_instance.instance_id, svgp_instance.data_id,
    )
    # insert records into database - data & model go first, then instance, then result
    model_data.update_remote_tables()
    aq_model_params.update_remote_tables()
    svgp_instance.update_remote_tables()
    result.update_remote_tables()
    print("Instance id:", svgp_instance.instance_id)


if __name__ == "__main__":
    main()

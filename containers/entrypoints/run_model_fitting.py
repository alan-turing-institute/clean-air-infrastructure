"""
Model fitting
"""
import os
import logging
import pickle
from datetime import datetime
from cleanair.models import ModelData, SVGP, MRDGP
from cleanair.loggers import get_log_level
from cleanair.parsers import ModelFitParser
from cleanair.parsers import get_data_config_from_kwargs


def write_predictions_to_file(y_pred, results_dir, filename):
    """Write a prediction dict to pickle."""
    pred_filepath = os.path.join(results_dir, filename)
    with open(pred_filepath, "wb") as handle:
        pickle.dump(y_pred, handle)


def main():  # pylint: disable=R0914
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ModelFitParser(description="Run model fitting")

    # Parse and interpret arguments
    kwargs = parser.parse_kwargs()

    # Update database/write to file
    no_db_write = kwargs.pop("no_db_write")
    local_write = kwargs.pop("local_write")
    local_read = kwargs.pop("local_read")
    predict_write = kwargs.pop("predict_write")
    results_dir = kwargs.pop("results_dir")
    model_dir = kwargs.pop("model_dir")
    predict_training = kwargs.pop("predict_training")
    model_name = kwargs.pop('model_name')

    # Experiment config
    xp_config = dict(
        name=model_name,
        restore=False,
        model_state_fp=model_dir,
        save_model_state=False,
    )

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # get the model config from the parser arguments
    model_config = get_data_config_from_kwargs(kwargs)

    if "aqe" in model_config["train_sources"] + model_config["pred_sources"]:
        raise NotImplementedError("AQE cannot currently be run. Coming soon")

    if model_config["species"] != ["NO2"]:
        raise NotImplementedError(
            "The only pollutant we can model right now is NO2. Coming soon"
        )

    #initialise the model

    models = {
        'svgp': SVGP,
        'mr_dgp': MRDGP,
    }

    if model_name not in models:
        raise NotImplementedError('Model {model} has not been implmented'.format(model=model_name))

    model_fitter = models[model_name](experiment_config=xp_config, batch_size=100)   
    model_fitter.model_params["maxiter"] = 1
    model_fitter.model_params["train"] = True
    model_fitter.model_params["restore"] = False

    # Get the model data
    if local_read:
        logging.info("Reading local data")
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

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
    logging.info(
        "Training the model for %s iterations.", model_fitter.model_params["maxiter"]
    )
    fit_start_time = datetime.now()
    model_fitter.fit(x_train, y_train)

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction
    y_test_pred = model_fitter.predict(x_test)
    if predict_training:
        x_train_pred = x_train.copy()
        if "satellite" in x_train:
            x_train_pred.pop("satellite")
        y_train_pred = model_fitter.predict(x_train_pred)

    # Internally update the model results in the ModelData object
    model_data.update_test_df_with_preds(y_test_pred, fit_start_time)

    # Write the model results to the database
    if not no_db_write:
        # see issue 103: generalise for multiple pollutants
        model_data.normalised_pred_data_df[
            "predict_mean"
        ] = model_data.normalised_pred_data_df["NO2_mean"]
        model_data.normalised_pred_data_df[
            "predict_var"
        ] = model_data.normalised_pred_data_df["NO2_var"]
        model_data.update_remote_tables()

    # Write the model results to file
    if predict_write:
        write_predictions_to_file(y_test_pred, results_dir, "test_pred.pickle")
        if predict_training:
            write_predictions_to_file(y_train_pred, results_dir, "train_pred.pickle")


if __name__ == "__main__":
    main()

"""
Model fitting
"""
from datetime import datetime
import logging
from cleanair.models import ModelData, SVGP
from cleanair.parsers import ModelFittingParser
from cleanair.instance import (
    AirQualityInstance,
    AirQualityModelParams,
    AirQualityResult,
)


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
    model_fitter.model_params["kernel"]["name"] = "matern32"

    # read data from db
    logging.info("Reading from database using data config.")
    model_data = ModelData(config=data_config, secretfile=args.secretfile)

    # get the training dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    x_train = training_data_dict["X"]
    y_train = training_data_dict["Y"]

    # train model
    fit_start_time = datetime.now()
    logging.info("Training model for %s iterations.", args.maxiter)
    model_fitter.fit(x_train, y_train)
    logging.info("Training completed")

    # TODO predict at both the training and test set!
    # predict either at the training or test set
    if args.predict_training:
        x_test = x_train.copy()
    else:
        predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]

    # Do prediction
    logging.info("Started predicting")
    y_pred = model_fitter.predict(x_test)
    logging.info("Finished predicting")

    # Create a results dataframe
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
    result = AirQualityResult(
        instance_id=svgp_instance.instance_id,
        data_id=svgp_instance.data_id,
        secretfile=args.secretfile,
        result_df=result_df,
    )
    # insert records into database - data & model go first, then instance, then result
    logging.info("Writing results to the databases.")
    model_data.update_remote_tables()
    aq_model_params.update_remote_tables()
    svgp_instance.update_remote_tables()
    result.update_remote_tables()
    logging.info("Instance id is %s", svgp_instance.instance_id)


if __name__ == "__main__":
    main()

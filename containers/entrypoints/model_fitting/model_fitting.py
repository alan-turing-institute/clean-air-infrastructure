"""
Model fitting
"""
from datetime import datetime
from cleanair.models import ModelData, SVGP
from cleanair.parsers import ModelFittingParser
from cleanair.instance import (
    AirQualityInstance,
    AirQualityModelParams,
    AirQualityResult,
)
from cleanair.loggers import initialise_logging


def main():  # pylint: disable=R0914
    """
    Run model fitting
    """
    # Parse and interpret command line arguments
    parser = ModelFittingParser(description="Run model fitting")
    args = parser.parse_args()
    logger = initialise_logging(args.verbose)

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
    logger.info("Reading from database using data config.")
    model_data = ModelData(config=data_config, secretfile=args.secretfile)

    # get the training dictionaries




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
    logger.info("Writing results to the databases.")
    model_data.update_remote_tables()
    aq_model_params.update_remote_tables()
    svgp_instance.update_remote_tables()
    result.update_remote_tables()
    logger.info("Instance id is %s", svgp_instance.instance_id)


if __name__ == "__main__":
    main()

"""
Model fitting
"""
import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers/')
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.models import ModelData, ModelFitting


def main():
    """
    Extract static features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Run model fitting")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-b", "--start", type=str, default='2019-10-25 00:00:00', help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for.")   
    parser.add_argument("-e", "--end", type=str, default='2019-10-28 00:00:00', help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for.")   
    
    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    start = kwargs.pop('start')    
    end = kwargs.pop('end')

    try:
       model_data = ModelData(**kwargs)
    #    data_df, X, Y = model_data.get_model_inputs(start_date=start, end_date=end, norm_by='laqn', sources=['laqn', 'aqe'], species=['NO2'])
       
    #    model_fitter = ModelFitting(X=X, Y=Y)
    #    model_fitter.model_fit()
       model_data.viz_sensor_data(start_date=start, end_date=end, source='laqn', species='NO2')
    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()

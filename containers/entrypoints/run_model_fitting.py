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
    parser.add_argument("-e", "--end", type=str, default='2019-10-26 00:00:00', help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for.")   
    
    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    start = kwargs.pop('start')    
    end = kwargs.pop('end')

   
    # Get the model data
    model_data = ModelData(**kwargs)
    model_data_df = model_data.get_model_inputs(start_date=start,
                                                end_date=end, 
                                                sources=['laqn', 'aqe'], 
                                                species=['NO2'])
    
#    Fit the model
    model_fitter = ModelFitting()
    model_fitter.model_fit(data=model_data_df, x_names = [], y_names=['NO2'], n_iter=10)

    # #    Do prediction and write to database
    predict_df = model_fitter.model_predict(model_data_df)
    print(predict_df)
    


if __name__ == "__main__":
    main()

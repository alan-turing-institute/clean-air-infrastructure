import os
from datetime import datetime
import pickle
import gpflow
import json
import numpy as np

## Save model and X,Y arrays to file
def save_model_and_metadata(
        scoot_id: str,
        model,
        X_array,
        Y_array,
        start_date: str,
        end_date: str,
        kernelsettings: dict,
        scootsettings: dict,
        dir_path = 'data/models'
    ):

    # Replace / with _
    scoot_id = scoot_id.replace('/','_')
    
    # Convert start and end dates to datetime
    start_date = datetime.strptime(start_date,'%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date,'%Y-%m-%d %H:%M:%S')
    
    # Get date range from start and end dates
    date_range = str(start_date.day) + start_date.strftime("%b") + '_' + str(end_date.day) + end_date.strftime("%b")
    
    path_to_file = os.path.join(dir_path,scoot_id,date_range)
    print('Saving data to', path_to_file)

    # Create directory if necessary
    if not os.path.exists(path_to_file):
        os.makedirs(path_to_file)
    
    # Create model copy
    model_copy = gpflow.utilities.deepcopy_components(model)
    # Save model to file
    pickle.dump( model_copy, open( os.path.join(path_to_file,'model.h5'), "wb" ) )
    
    # Save X and Y arrays to file
    print(os.path.join(path_to_file,'Y.npy'))
    np.save(os.path.join(path_to_file,'X.npy'), X_array)
    np.save(os.path.join(path_to_file,'Y.npy'), Y_array)
    
    # Create metadata dictionary to store as json
    metadata = {}
    
    # Store kernel and scoot settings
    metadata['kernel_settings'] = kernelsettings
    metadata['scoot_settings'] = scootsettings
    
    # Store start and end dates
    metadata['start_date'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
    metadata['end_date'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
    metadata['scoot_id'] = scoot_id
    
    # Save metadata as json
    with open(os.path.join(path_to_file,('metadata.json')), 'w') as json_file:
        json.dump(metadata, json_file)


## Load model and X,Y arrays from file
def load_model_and_metadata(
        scoot_id: str,
        date_range: str = '10feb_16feb',
        dir_path="data/models"
    ):
    
    # Specify path to folder and file
    dir_path = '/data/models'
    
    # Replace / with _
    scoot_id = scoot_id.replace('/','_')
    
    # Specify path to folder
    dir_path = os.path.join(dir_path,scoot_id ,date_range)

    # Load model
    model = pickle.load(open(os.path.join(dir_path,'model.h5'), "rb" ))
                       
    # Load X and Y arrays to file
    X_array = np.load(os.path.join(dir_path,'X.npy'))
    Y_array = np.load(os.path.join(dir_path,'Y.npy'))
    
    # Load metadata
    with open(os.path.join(dir_path,'metadata.json')) as json_file:
        metadata = json.load(json_file)
    
    return model,X_array,Y_array,metadata
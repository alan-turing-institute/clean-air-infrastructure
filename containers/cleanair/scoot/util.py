import os
from datetime import datetime
import pickle
import gpflow
import json
import numpy as np
from pathlib import Path


def generate_fp(name, xp_root="experiments", folder="data", prefix="normal", postfix="scoot", extension="csv"):
    return os.path.join(xp_root, name, folder, prefix + "_" + postfix + "." + extension)

def save_model_to_file(model, name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Save model using pickle.
    """
    # Create model copy
    model_copy = gpflow.utilities.deepcopy_components(model)
    # Save model to file
    detector_id = detector_id.replace('/', '_')
    filepath = os.path.join(xp_root, name, "models")
    Path(filepath).mkdir(exist_ok=True)
    filepath = generate_fp(name, xp_root, "models", prefix, detector_id, ".h5")
    pickle.dump(model_copy, open(filepath), "wb")

def save_results_to_file(y_pred, name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Save results to npy with pickle.
    """
    filepath = generate_fp(
        name, xp_root, "results", prefix, detector_id.replace('/', '_'), "npy"
    )
    np.save(filepath, y_pred)

def save_processed_data_to_file(
        X, Y, name, detector_id, xp_root="experiments", prefix="normal"
    ):
    """
    Save processed data for a single detector to file.
    """
    x_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_X", "npy"
    )
    y_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_Y", "npy"
    )
    np.save(X, x_filepath)
    np.save(Y, y_filepath)

def load_model_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """Load model from pickle."""
    filepath = generate_fp(name, xp_root, "models", prefix, detector_id, ".h5")
    return pickle.load(open(filepath, "rb"))

def load_results_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """Load results of predictions from model."""
    filepath = generate_fp(
        name, xp_root, "results", prefix, detector_id.replace('/', '_'), "npy"
    )
    return np.load(filepath)

def load_processed_data_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Load X and Y from file.
    """
    x_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_X", "npy"
    )
    y_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_Y", "npy"
    )
    return np.load(x_filepath), np.load(y_filepath)

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
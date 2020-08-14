
from datetime import datetime

import pandas as pd
import numpy as np
import pytest

from odysseus.databases import TrafficQuery
from cleanair.utils import get_git_hash, instance_id_from_hash, hash_dict

@pytest.fixture(scope="function")
def scoot_detectors(scoot_offset, scoot_limit, borough, secretfile):

    traffic_query = TrafficQuery(secretfile=secretfile)
    detectors = traffic_query.scoot_detectors(offset=scoot_offset, limit=scoot_limit, borough=borough, output_type="df")['detector_id']
    return list(detectors)

@pytest.fixture(scope="function")
def frame(scoot_detectors, scoot_start, scoot_upto):

    num_detectors = len(scoot_detectors)

    fmt = "%Y-%m-%dT%H:%M:%S"
    start_time = scoot_start
    upto_time = scoot_upto
    model_name = 'svgp'
    preprocessing = {'features': ['time_norm'],
                     'median': False,
                     'normaliseby': 'clipped_hour',
                     'target': ['n_vehicles_in_interval']}
    model_params = {'n_inducing_points': None,
                    'inducing_point_method': 'random',
                    'maxiter': 2000,
                    'model_name': model_name,
                    'kernel': {'name': 'rbf',
                               'hyperparameters': {'lengthscales': 1.0, 'variance': 1.0}}}
    fit_start_time = datetime.now().strftime(fmt)
    cluster_id = 'local'

    # create rows ready for dataframe
    dframe = pd.DataFrame()
    dframe["data_config"] = [
        dict(detectors=[d], start_time=start_time, end_time=upto_time)
        for d in scoot_detectors
    ]
    dframe["preprocessing"] = np.repeat(preprocessing, num_detectors)
    dframe["model_param"] = np.repeat(model_params, num_detectors)
    dframe["model_name"] = model_name
    dframe["fit_start_time"] = fit_start_time
    dframe["cluster_id"] = cluster_id
    dframe["param_id"] = dframe["model_param"].apply(hash_dict)
    dframe["data_id"] = dframe["data_config"].apply(hash_dict)
    dframe["git_hash"] = get_git_hash()
    dframe["instance_id"] = dframe.apply(lambda x: instance_id_from_hash(x.model_name, x.param_id, x.data_id, x.git_hash), axis=1)

    return dframe

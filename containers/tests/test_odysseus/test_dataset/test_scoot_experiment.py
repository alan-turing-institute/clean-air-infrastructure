
from typing import List

import pandas as pd
import numpy as np
import gpflow

from odysseus.experiment import ScootExperiment
from odysseus.experiment.utils import load_gpflow2_model_from_file
from odysseus.dataset import ScootDataset


def test_scoot_experiment(scoot_dataset: ScootDataset, frame: pd.DataFrame, secretfile: str) -> None:

    datasets = scoot_dataset.split_by_detector()
    assert np.all([isinstance(dataset, ScootDataset) for dataset in datasets])

    # Pick first dataset for training
    frame_sample = frame.head(1)
    dataset_sample = datasets[0]

    # Keep back input data for testing loaded model later
    X = dataset_sample.features_tensor

    # File path variables
    model_dir = 'gpflow2_models/'
    instance_id = frame_sample.at[0, 'instance_id']

    # Init a ScootExperiment
    scoot_xp = ScootExperiment(frame=frame_sample, secretfile=secretfile)

    # Trains and saves model(s) to file
    models = scoot_xp.train_models([dataset_sample], dryrun=False)

    assert np.all([isinstance(model, gpflow.models.GPModel) for model in models])

    # Re-load the model
    export_dir = model_dir + instance_id
    loaded_model = load_gpflow2_model_from_file(export_dir)

    original_result = models[0].predict_f(X)
    loaded_result = loaded_model.predict(X)

    # Ensure results agree
    np.testing.assert_array_equal(loaded_result, original_result)

"""Loading and saving files."""

import os
import pickle
import logging
from typing import Iterable


def load_models_from_file(instances: Iterable, path_to_models: str) -> dict:
    """
    Load models from a directory.

    Args:
        instances: Instance ids to load models for.
        path_to_models: Path to directory of models.

    Returns:
        GPflow trained models.
    """
    models = dict()
    missing_files = 0
    logging.info("Loading models from %s", path_to_models)
    for instance_id in instances:
        try:
            filepath = os.path.join(path_to_models, instance_id + ".h5")
            models[instance_id] = pickle.load(open(filepath, "rb"))
        except FileNotFoundError:
            missing_files += 1

    if missing_files:
        logging.error(
            "%s missing model files out of %s.", missing_files, len(instances)
        )
    return models

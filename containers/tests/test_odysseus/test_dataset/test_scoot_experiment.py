
from typing import List

import pandas as pd

from odysseus.experiment import ScootExperiment
from odysseus.dataset import ScootDataset


def test_scoot_experiment(scoot_dataset: ScootDataset, frame: pd.DataFrame, secretfile: str):

    datasets = scoot_dataset.split_by_detector()
    scoot_xp = ScootExperiment(frame=frame, secretfile=secretfile)

    models = scoot_xp.train_models(datasets, dryrun=False)
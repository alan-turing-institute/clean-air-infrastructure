"""Tests for ScootExperiment class"""

from typing import List

from odysseus.experiment import ScootExperiment

def test_scoot_experiment(scoot_xp: ScootExperiment, scoot_detectors: List[str], scoot_start: str, scoot_upto: str):

    datasets = scoot_xp.load_datasets(scoot_detectors, scoot_start, scoot_upto)
    model_list = scoot_xp.train_models(datasets, dryrun=False)

    print(datasets)
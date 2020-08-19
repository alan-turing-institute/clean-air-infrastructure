"""Tests for ScootExperiment class"""

from typing import List

from odysseus.experiment import ScootExperiment 



def test_scoot_experiment(scoot_xp: ScootExperiment, detectors: List[str], train_start: str, train_upto: str, scoot_config, scoot_dataset):

    print(scoot_config.__dict__)
    print(scoot_dataset.__dict__)
    print(scoot_config.dict())
    datasets = scoot_dataset.split_by_detector()
    print(datasets)
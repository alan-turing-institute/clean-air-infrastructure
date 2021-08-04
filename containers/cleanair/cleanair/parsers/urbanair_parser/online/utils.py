from enum import Enum
from pathlib import Path

from ..experiment.main import metrics, run, setup, update, upload
from ....types import ExperimentName


class StaticDynamic(str, Enum):
    """Is the model static or dynamic?"""

    dynamic = "dynamic"
    static = "static"


def run_experiment_online(experiment_name: ExperimentName, experiment_root: Path):
    setup(experiment_name, experiment_root=experiment_root)
    run(experiment_name, experiment_root=experiment_root)
    update(experiment_name, experiment_root=experiment_root)
    metrics(experiment_name, experiment_root=experiment_root)
    upload(experiment_name, experiment_root=experiment_root)

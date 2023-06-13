"""Archive and download model instances"""
from pathlib import Path

import typer
from cleanair_data.utils.file_manager import FileManager

from ..shared_args import ExperimentDir

app = typer.Typer(help="Access the model instance archive")


@app.command()
def upload(instance: Path = ExperimentDir) -> None:
    """Uploads an instance to the experiment archive"""

    FileManager(instance).upload()


@app.command()
def download(instance_id: str, target: Path = None) -> None:
    """Downloads an instance from the experiment archive"""

    if not target:
        target = Path(instance_id)

    FileManager(target, blob_id=instance_id)

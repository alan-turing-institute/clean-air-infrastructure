"""Settings for the Odysseus parser."""

from pathlib import Path
import typer

APP_NAME = "Odysseus"
APP_DIR: Path = Path(typer.get_app_dir(APP_NAME))
SCOOT_MODELLING: Path = APP_DIR / "scoot_modelling"

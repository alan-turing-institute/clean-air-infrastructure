"""CLI state"""
from typing import Dict, Union, Optional
from logging import Logger
from .configuration import CONFIG_SECRETFILE_PATH

# pylint: disable=C0103
state: Dict[str, Union[bool, str, Optional[Logger]]] = {
    "verbose": False,
    "secretfile": str(CONFIG_SECRETFILE_PATH),
    "logger": None,
}

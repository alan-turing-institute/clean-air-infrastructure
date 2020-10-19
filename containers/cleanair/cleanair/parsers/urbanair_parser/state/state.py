"""CLI state"""
from typing import Dict, Union, Optional
from logging import Logger

# pylint: disable=C0103
state: Dict[str, Union[bool, str, Optional[Logger]]] = {
    "verbose": False,
    "secretfile": "",
    "logger": None,
}

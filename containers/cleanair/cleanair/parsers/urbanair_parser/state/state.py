"""CLI state"""
from typing import Dict, Union

# pylint: disable=C0103
state: Dict[str, Union[bool, str]] = {"verbose": False, "secretfile": ""}

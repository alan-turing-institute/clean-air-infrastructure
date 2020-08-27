"""Types for models and parameters."""

from typing import Dict, Union
from ..utils import hash_fn

ModelParams = Dict[str, Union[float, bool, int, Dict, None]]

class ParamIdMixin:
    """Add function for creating a param id."""

    def param_id(self):
        """Return a hashed param id."""
        return hash_fn(self.json(sort_keys=True))

"""Generalised mixin for model parameters."""

# from __future__ import annotations
# from typing import TYPE_CHECKING
from abc import abstractmethod
from ..utils.hashing import hash_dict
from ..databases.mixins import ModelTableMixin

# if TYPE_CHECKING:
from ..types import ParamsDict


class ModelParamsMixin:
    """Parameters of an air quality model."""

    def __init__(
        self, secretfile: str, model_name: str, model_params: ParamsDict, **kwargs,
    ):
        super().__init__(secretfile=secretfile, **kwargs)
        self.model_name = model_name
        self.model_params = model_params

    @property
    def param_id(self) -> str:
        """Parameter id of the hashed model params dict."""
        return hash_dict(self.model_params)

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """The model table to read and write from.

        Returns:
            A sqlalchemy table that extends ModelTableMixin.
        """

    def update_remote_tables(self):
        """Write the air quality model parameters to the database."""
        records = [
            dict(
                model_name=self.model_name,
                model_param=self.model_params,
                param_id=self.param_id,
            )
        ]
        self.commit_records(records, table=self.model_table, on_conflict="ignore")

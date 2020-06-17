"""Class for writing model params to the DB."""

from __future__ import annotations
from typing import TYPE_CHECKING
from .params import ModelParamsMixin
from ..databases import DBWriter
from ..databases.tables import AirQualityModelTable

if TYPE_CHECKING:
    from ..types import ParamsSVGP


class AirQualityModelParams(ModelParamsMixin, DBWriter):
    """Model parameters for an air quality model"""

    def __init__(
        self, secretfile: str, model_name: str, model_params: ParamsSVGP, **kwargs,
    ):
        super().__init__(
            secretfile=secretfile,
            model_name=model_name,
            model_params=model_params,
            **kwargs,
        )

    @property
    def model_table(self) -> AirQualityModelTable:
        """The air quality model table."""
        return AirQualityModelTable

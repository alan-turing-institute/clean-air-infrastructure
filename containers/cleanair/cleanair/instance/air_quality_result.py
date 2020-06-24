"""An air quality result."""

from typing import Optional, Union, List
import pandas as pd
from ..databases import DBWriter
from ..mixins import ResultMixin
from ..databases.tables import AirQualityResultTable
from ..types import Source

class AirQualityResult(ResultMixin, DBWriter):
    """Air quality predictions from a trained model."""

    def __init__(
        self,
        instance_id: str,
        data_id: str,
        secretfile: str,
        result_df: Optional[pd.DataFrame],
        **kwargs,
    ):
        super().__init__(
            instance_id=instance_id,
            data_id=data_id,
            secretfile=secretfile,
            result_df=result_df,
        )

    @property
    def result_table(self) -> AirQualityResultTable:
        """Air quality result table."""
        return AirQualityResultTable

"""An air quality result."""

from typing import Optional
import pandas as pd
from ..databases import DBWriter
from ..mixins import ResultMixin
from ..databases.tables import AirQualityResultTable


class AirQualityResult(ResultMixin, DBWriter):
    """Air quality predictions from a trained model."""

    def __init__(
        self,
        instance_id: str,
        data_id: str,
        result_df: Optional[pd.DataFrame],
        secretfile: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            instance_id=instance_id,
            data_id=data_id,
            secretfile=secretfile,
            result_df=result_df,
            **kwargs
        )

    @property
    def result_table(self) -> AirQualityResultTable:
        """Air quality result table."""
        return AirQualityResultTable

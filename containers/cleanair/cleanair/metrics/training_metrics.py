"""Metrics to measure how the model has trained"""

from datetime import datetime
from pydantic import BaseModel


class TrainingMetrics(BaseModel):
    """Training metrics for an air quality model"""

    fit_end_time: datetime
    fit_start_time: datetime
    instance_id: str

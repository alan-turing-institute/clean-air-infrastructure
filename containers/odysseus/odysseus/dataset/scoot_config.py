"""Config settings for scoot data."""

from typing import List, Optional
from pydantic import BaseModel


class ScootConfig(BaseModel):
    """Scoot data config."""

    detectors: Optional[List[str]]
    limit: Optional[int]
    offset: Optional[int]
    start: str
    upto: str


class ScootPreprocessing(BaseModel):
    """Scoot preprocessing settings for a model."""

    datetime_transformation: str
    features: List[str]
    normalise_datetime: bool
    target: List[str]

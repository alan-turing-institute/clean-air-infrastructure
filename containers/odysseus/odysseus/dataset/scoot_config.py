"""Config settings for scoot data."""

from typing import List
from pydantic import BaseModel

class ScootConfig(BaseModel):
    """Scoot data config."""

    detectors: List[str]
    start: str
    upto: str

class ScootPreprocessing(BaseModel):
    """Scoot preprocessing settings for a model."""

    features: List[str]
    target: List[str]

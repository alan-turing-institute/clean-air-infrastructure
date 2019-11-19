"""
Scoot feature extraction
"""
from sqlalchemy import between, cast, func, Integer, literal, or_
from .static_features import StaticFeatures
from .feature_funcs import sum_area
from ..databases.tables import UKMap

class ScootFeatures(StaticFeatures):
    """Extract features for UKMap"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.features = {}
"""
Street Canyon feature extraction
"""
from .feature_extractor import FeatureExtractor
from .feature_funcs import min_, avg_, max_
from ..databases.tables import StreetCanyon


class StreetCanyonFeatures(FeatureExtractor):
    """Extract features for StreetCanyon"""

    @property
    def table(self):
        return StreetCanyon

    @property
    def feature_source(self):
        return "streetcanyon"

    @property
    def features(self):
        return {
            "min_canyon_ratio": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": min_,
            },
            "avg_canyon_ratio": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": avg_,
            },
            "max_canyon_ratio": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": max_,
            },
            "min_canyon_narrowest": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": min_,
            },
            "avg_canyon_narrowest": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": avg_,
            },
            "max_canyon_narrowest": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": max_,
            },
        }

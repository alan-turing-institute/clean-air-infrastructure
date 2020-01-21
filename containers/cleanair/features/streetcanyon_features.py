"""
Street Canyon feature extraction
"""
from .features import Features
from .feature_funcs import min_, avg_, max_
from ..databases.tables import StreetCanyon


class StreetCanyonFeatures(Features):
    """Extract features for StreetCanyon"""

    @property
    def table(self):
        return StreetCanyon

    @property
    def features(self):
        return {
            "min_ratio_avg": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": min_,
            },
            "avg_ratio_avg": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": avg_,
            },
            "max_ratio_avg": {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": max_,
            },
            "min_min_width": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": min_,
            },
            "avg_min_width": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": avg_,
            },
            "max_min_width": {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": max_,
            },
        }

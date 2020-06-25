"""
Methods for evaluating metrics of a model fit.
"""

from .evaluate import evaluate_model_data
from .evaluate import get_metric_methods
from .evaluate import get_precision_methods
from .evaluate import measure_scores_on_groupby
from .precision import probable_error
from .precision import confidence_interval
from .precision import confidence_interval_50
from .precision import confidence_interval_75
from .precision import confidence_interval_95

__all__ = [
    "evaluate_model_data",
    "get_metric_methods",
]

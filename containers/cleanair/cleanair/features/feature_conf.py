"""
Street Canyon feature extraction
"""

from ..databases.tables import StreetCanyon, OSHighway, UKMap
from .feature_funcs import sum_length, avg_, min_, max_, sum_area

FEATURE_CONFIG = {
    "streetcanyon": {
        "table": StreetCanyon,
        "features": {
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
        },
    },
    "oshighway": {
        "table": OSHighway,
        "features": {
            "total_road_length": {
                "type": "geom",
                "feature_dict": {},
                "aggfunc": sum_length,
            },
            "total_a_road_primary_length": {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road Primary"]},
                "aggfunc": sum_length,
            },
            "total_a_road_length": {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road"]},
                "aggfunc": sum_length,
            },
            "total_b_road_length": {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["B Road", "B Road Primary"]},
                "aggfunc": sum_length,
            },
            "total_length": {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["*"]},
                "aggfunc": sum_length,
            },
        },
    },
    "ukmap": {
        "table": UKMap,
        "features": {
            "building_height": {
                "type": "value",
                "feature_dict": {"calculated_height_of_building": ["*"]},
                "aggfunc": max_,
            },
            "flat": {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated", "Water"]},
                "aggfunc": sum_area,
            },
            "grass": {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated"]},
                "aggfunc": sum_area,
            },
            "hospitals": {
                "type": "geom",
                "feature_dict": {"landuse": ["Hospitals"]},
                "aggfunc": sum_area,
            },
            "museums": {
                "type": "geom",
                "feature_dict": {"landuse": ["Museum"]},
                "aggfunc": sum_area,
            },
            "park": {
                "type": "geom",
                "feature_dict": {
                    "feature_type": ["Vegetated"],
                    "landuse": ["Recreational open space"],
                },
                "aggfunc": sum_area,
            },
            "water": {
                "type": "geom",
                "feature_dict": {"feature_type": ["Water"]},
                "aggfunc": sum_area,
            },
        },
    },
}

ALL_FEATURES = [
    val
    for sublist in [
        list(j.keys()) for j in [ftype["features"] for ftype in FEATURE_CONFIG.values()]
    ]
    for val in sublist
]

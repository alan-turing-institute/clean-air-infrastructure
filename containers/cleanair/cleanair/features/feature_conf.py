"""
Street Canyon feature extraction
"""
from ..databases.tables import StreetCanyon, OSHighway, UKMap
from .feature_funcs import sum_length, avg_, min_, max_, sum_area
from ..types import FeatureNames, DynamicFeatureNames


FEATURE_CONFIG = {
    "streetcanyon": {
        "table": StreetCanyon,
        "features": {
            FeatureNames.min_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": min_,
            },
            FeatureNames.avg_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": avg_,
            },
            FeatureNames.max_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": max_,
            },
            FeatureNames.min_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": min_,
            },
            FeatureNames.avg_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": avg_,
            },
            FeatureNames.max_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": max_,
            },
        },
    },
    "oshighway": {
        "table": OSHighway,
        "features": {
            FeatureNames.total_road_length.value: {
                "type": "geom",
                "feature_dict": {},
                "aggfunc": sum_length,
            },
            FeatureNames.total_a_road_primary_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road Primary"]},
                "aggfunc": sum_length,
            },
            FeatureNames.total_a_road_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road"]},
                "aggfunc": sum_length,
            },
            FeatureNames.total_b_road_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["B Road", "B Road Primary"]},
                "aggfunc": sum_length,
            },
            FeatureNames.total_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["*"]},
                "aggfunc": sum_length,
            },
        },
    },
    "ukmap": {
        "table": UKMap,
        "features": {
            FeatureNames.building_height.value: {
                "type": "value",
                "feature_dict": {"calculated_height_of_building": ["*"]},
                "aggfunc": max_,
            },
            FeatureNames.flat.value: {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated", "Water"]},
                "aggfunc": sum_area,
            },
            FeatureNames.grass.value: {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated"]},
                "aggfunc": sum_area,
            },
            FeatureNames.hospitals.value: {
                "type": "geom",
                "feature_dict": {"landuse": ["Hospitals"]},
                "aggfunc": sum_area,
            },
            FeatureNames.museums.value: {
                "type": "geom",
                "feature_dict": {"landuse": ["Museum"]},
                "aggfunc": sum_area,
            },
            FeatureNames.park.value: {
                "type": "geom",
                "feature_dict": {
                    "feature_type": ["Vegetated"],
                    "landuse": ["Recreational open space"],
                },
                "aggfunc": sum_area,
            },
            FeatureNames.water.value: {
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

FEATURE_CONFIG_DYNAMIC = {
    "scoot": {
        "table": OSHighway,
        "features": {
            DynamicFeatureNames.max_n_vehicles.value: {
                "type": "value",
                "feature_dict": {"n_vehicles_in_interval": ["*"]},
                "aggfunc": max_,
            },
            DynamicFeatureNames.avg_n_vehicles.value: {
                "type": "value",
                "feature_dict": {"n_vehicles_in_interval": ["*"]},
                "aggfunc": avg_,
            },
            DynamicFeatureNames.min_n_vehicles.value: {
                "type": "value",
                "feature_dict": {"n_vehicles_in_interval": ["*"]},
                "aggfunc": min_,
            },
        },
    }
}

ALL_FEATURES = [
    val
    for sublist in [
        list(j.keys()) for j in [ftype["features"] for ftype in FEATURE_CONFIG.values()]
    ]
    for val in sublist
]

ALL_FEATURES_DYNAMIC = [
    val
    for sublist in [
        list(j.keys())
        for j in [ftype["features"] for ftype in FEATURE_CONFIG_DYNAMIC.values()]
    ]
    for val in sublist
]

"""
Street Canyon feature extraction
"""
from ..databases.tables import StreetCanyon, OSHighway, UKMap
from .feature_funcs import sum_length, avg_, min_, max_, sum_area
from ..types import StaticFeatureNames, DynamicFeatureNames


FEATURE_CONFIG = {
    "streetcanyon": {
        "table": StreetCanyon,
        "features": {
            StaticFeatureNames.min_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": min_,
            },
            StaticFeatureNames.avg_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": avg_,
            },
            StaticFeatureNames.max_canyon_ratio.value: {
                "type": "value",
                "feature_dict": {"ratio_avg": ["*"]},
                "aggfunc": max_,
            },
            StaticFeatureNames.min_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": min_,
            },
            StaticFeatureNames.avg_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": avg_,
            },
            StaticFeatureNames.max_canyon_narrowest.value: {
                "type": "value",
                "feature_dict": {"min_width": ["*"]},
                "aggfunc": max_,
            },
        },
    },
    "oshighway": {
        "table": OSHighway,
        "features": {
            StaticFeatureNames.total_road_length.value: {
                "type": "geom",
                "feature_dict": {},
                "aggfunc": sum_length,
            },
            StaticFeatureNames.total_a_road_primary_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road Primary"]},
                "aggfunc": sum_length,
            },
            StaticFeatureNames.total_a_road_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["A Road"]},
                "aggfunc": sum_length,
            },
            StaticFeatureNames.total_b_road_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["B Road", "B Road Primary"]},
                "aggfunc": sum_length,
            },
            StaticFeatureNames.total_length.value: {
                "type": "geom",
                "feature_dict": {"route_hierarchy": ["*"]},
                "aggfunc": sum_length,
            },
        },
    },
    "ukmap": {
        "table": UKMap,
        "features": {
            StaticFeatureNames.building_height.value: {
                "type": "value",
                "feature_dict": {"calculated_height_of_building": ["*"]},
                "aggfunc": max_,
            },
            StaticFeatureNames.flat.value: {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated", "Water"]},
                "aggfunc": sum_area,
            },
            StaticFeatureNames.grass.value: {
                "type": "geom",
                "feature_dict": {"feature_type": ["Vegetated"]},
                "aggfunc": sum_area,
            },
            StaticFeatureNames.hospitals.value: {
                "type": "geom",
                "feature_dict": {"landuse": ["Hospitals"]},
                "aggfunc": sum_area,
            },
            StaticFeatureNames.museums.value: {
                "type": "geom",
                "feature_dict": {"landuse": ["Museum"]},
                "aggfunc": sum_area,
            },
            StaticFeatureNames.park.value: {
                "type": "geom",
                "feature_dict": {
                    "feature_type": ["Vegetated"],
                    "landuse": ["Recreational open space"],
                },
                "aggfunc": sum_area,
            },
            StaticFeatureNames.water.value: {
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

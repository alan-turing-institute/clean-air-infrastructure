"""Misc types"""
from enum import Enum, unique
from typing import Any, Dict, List, Union


# pylint: disable=invalid-name
@unique
class DetectionClass(str, Enum):
    """Possible JamCam detection Types"""

    all_classes = "all"
    truck = "trucks"
    person = "people"
    car = "cars"
    motorbike = "motorbikes"
    bicycle = "bicycles"
    bus = "buses"

    @classmethod
    def map_detection_class(cls, detection_class: str) -> str:
        """Map a API name to a database entry"""
        map_classes = {
            "all": "all",
            "trucks": "truck",
            "people": "person",
            "cars": "car",
            "motorbikes": "motorbike",
            "bicycles": "bicycle",
            "buses": "bus",
        }

        return map_classes[detection_class]

    @classmethod
    def map_all(cls) -> List[str]:
        """Return a list of 'all' types mapped"""

        return [cls.map_detection_class(i) for i in cls if i != cls.all_classes]


JSONType = Union[Dict[str, Any], List[Dict[str, Any]]]

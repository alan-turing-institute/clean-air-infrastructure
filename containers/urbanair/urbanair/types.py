from enum import Enum


class DetectionClass(str, Enum):

    all_classes = "all"
    truck = "trucks"
    person = "people"
    car = "cars"
    motorbike = "motorbikes"
    bus = "buses"

    @classmethod
    def map_detection_class(cls, detection_class):

        map_classes = {
            "all": "all",
            "trucks": "trucks",
            "people": "person",
            "cars": "car",
            "motorbikes": "motorbike",
            "buses": "bus",
        }

        return map_classes[detection_class]

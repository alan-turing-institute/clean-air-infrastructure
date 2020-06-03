<<<<<<< HEAD
from .scoot_queries import (
    ScootHourly,
    ScootDailyPerc,
    ScootDaily,
    ScootHourlyAvailability,
    ScootPercAvailability,
)

__all__ = [
    "ScootHourly",
    "ScootHourlyAvailability",
    "ScootDailyPerc",
    "ScootPercAvailability",
    "ScootDaily",
]
=======
from .scoot_queries import (
    ScootHourly,
    ScootDailyPerc,
    ScootDaily,
    ScootHourlyAvailability,
    ScootPercAvailability,
)
from .cam_queries import CamRecent, CamsSnapshot

__all__ = [
    "ScootHourly",
    "ScootHourlyAvailability",
    "ScootDailyPerc",
    "ScootPercAvailability",
    "ScootDaily",
    "CamRecent",
    "CamsSnapshot",
]
>>>>>>> 566626e3b8beb34ade921a178a3b33a981c759c5

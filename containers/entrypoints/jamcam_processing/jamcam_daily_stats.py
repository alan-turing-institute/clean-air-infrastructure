#!/usr/bin/env python

import cProfile

import datetime
import sys

from cleanair.databases.tables import JamCamDayStats
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import sessionmaker, Session
from urbanair.config import get_settings
from urbanair.databases.queries import get_jamcam_hourly
from urbanair.types import DetectionClass

SOURCE = 1

DB_SECRETS_FILE = get_settings().db_secret_file
DB_CONNECTION_STRING = DBConnectionMixin(DB_SECRETS_FILE)
DB_ENGINE = create_engine(DB_CONNECTION_STRING.connection_string, convert_unicode=True)
DeferredReflection.prepare(DB_ENGINE)
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=DB_ENGINE)

detection_classes = [
    DetectionClass("people"),
    DetectionClass("trucks"),
    DetectionClass("cars"),
    DetectionClass("motorbikes"),
    DetectionClass("bicycles"),
    DetectionClass("buses"),
]

detection_class_map = {
    "people": "person",
    "trucks": "truck",
    "cars": "car",
    "motorbikes": "motorbike",
    "bicycles": "bicycle",
    "buses": "bus",
}

session: Session = SESSION_LOCAL()

date = datetime.date.today() - datetime.timedelta(days=1)

data = {}
for detection_class in detection_classes:
    detection_class_string = detection_class_map[detection_class]
    query = get_jamcam_hourly(
        session, camera_id=None, detection_class=detection_class, starttime=date,
    )
    result = query.all()

    for row in result:
        if row.camera_id not in data.keys():
            data[row.camera_id] = {}
        if detection_class_string not in data[row.camera_id].keys():
            data[row.camera_id][detection_class_string] = []
        data[row.camera_id][detection_class_string].append(row.counts)

for camera_id, counts_per_class in data.items():
    all_counts = []
    for detection_class_string, counts in counts_per_class.items():
        count = sum(counts) / len(counts)
        all_counts.append(count)
        session.add(
            JamCamDayStats(
                camera_id=camera_id,
                detection_class=detection_class_string,
                date=date,
                count=count,
                source=SOURCE,
            )
        )
    count = sum(all_counts) / len(all_counts)
    session.add(
        JamCamDayStats(
            camera_id=camera_id,
            detection_class="all",
            date=date,
            count=count,
            source=SOURCE,
        )
    )

session.commit()

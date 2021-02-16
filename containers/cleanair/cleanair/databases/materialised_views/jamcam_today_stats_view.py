"""
Views of London boundary static data
"""

from sqlalchemy import func, literal
from sqlalchemy import select
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.sql.expression import union
from cleanair.databases.tables import JamCamVideoStats

from ..base import Base
from ..views import create_materialized_view


class JamcamTodayStatsView(Base):
    """View that contains an average of the day's detection count for each camera-class pair"""

    __table__ = create_materialized_view(
        name="today_stats_view",
        schema="jamcam",
        owner="jamcamwriter",
        selectable=union(
            select(
                [
                    JamCamVideoStats.camera_id.label("camera_id"),
                    func.avg(JamCamVideoStats.counts).label("counts"),
                    JamCamVideoStats.detection_class.label("detection_class"),
                    func.date_trunc(
                        "day", JamCamVideoStats.video_upload_datetime
                    ).label("measurement_start_utc"),
                ]
            )
            .where(
                JamCamVideoStats.video_upload_datetime
                >= func.date_trunc("day", current_timestamp())
            )
            .group_by(
                func.date_trunc("day", JamCamVideoStats.video_upload_datetime),
                JamCamVideoStats.camera_id,
                JamCamVideoStats.detection_class,
            ),
            select(
                [
                    JamCamVideoStats.camera_id.label("camera_id"),
                    func.avg(JamCamVideoStats.counts).label("counts"),
                    literal("all").label("detection_class"),
                    func.date_trunc(
                        "day", JamCamVideoStats.video_upload_datetime
                    ).label("measurement_start_utc"),
                ],
            )
            .where(
                JamCamVideoStats.video_upload_datetime
                >= func.date_trunc("day", current_timestamp())
            )
            .group_by(
                func.date_trunc("day", JamCamVideoStats.video_upload_datetime),
                JamCamVideoStats.camera_id,
            ),
        ),
        metadata=Base.metadata,
    )

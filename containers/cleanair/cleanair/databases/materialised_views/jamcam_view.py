"""
Views of Jamcam
"""
from cleanair.databases.tables import JamCamVideoStats
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import cast, Date

from ..base import Base
from ..views import create_materialized_view


class JamCamViewToday(Base):
	"""View of the interest points that gives London's boundary"""



	__table__ = create_materialized_view(
		name="jamcam_hourly_view_today",
		schema="jamcam",
		owner="refresher",
		selectable=select(
			[
				JamCamVideoStats.camera_id.label("camera_id"),
				func.avg(JamCamVideoStats.counts).label("counts"),
				JamCamVideoStats.detection_class.label("detection_class"),
				func.date_trunc("hour", JamCamVideoStats.video_upload_datetime).label("measurement_start_utc")
			]
		).where(
			cast(JamCamVideoStats.video_upload_datetime, Date) == func.current_date(),
		)
		.group_by(
			func.date_trunc("hour", JamCamVideoStats.video_upload_datetime),
			JamCamVideoStats.camera_id,
			JamCamVideoStats.detection_class,
		)
		.order_by(
			JamCamVideoStats.camera_id,
			func.date_trunc("hour", JamCamVideoStats.video_upload_datetime),
		),
		metadata=Base.metadata
	)

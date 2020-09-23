"""
Views of Jamcam
"""
from cleanair.databases.tables import JamCamVideoStats
from sqlalchemy import func
from sqlalchemy import select

from ..base import Base
from ..views import create_materialized_view


class JamCamView(Base):
	"""View of the interest points that gives London's boundary"""

	__table__ = create_materialized_view(
		name="jamcam_hourly_view",
		schema="jamcam",
		owner="refresher",
		selectable=select(
			[
				JamCamVideoStats.camera_id,
				func.avg(JamCamVideoStats.counts).label("counts"),
				JamCamVideoStats.detection_class,
				func.date_trunc("hour", JamCamVideoStats.video_upload_datetime).label(
					"measurement_start_utc"
				)
			]
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

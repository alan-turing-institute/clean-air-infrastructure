"""API database queries"""
from sqlalchemy import func
from sqlalchemy.exc import ProgrammingError
from cleanair.loggers import initialise_logging

# from cleanair.decorators import db_query
from .query_mixins import APIQueryMixin
import json


initialise_logging(verbosity=0)


class CamRecent(APIQueryMixin):
    def query(self, session, id):
        """
        return count data for an individual camera over historical time period
        """

        idparts = id.split(".")

        if (
            len(idparts[0]) != 5
            or len(idparts[1]) != 5
            or not idparts[0].isnumeric()
            or not idparts[1].isnumeric()
        ):
            return None
        res = session.execute(
            "select counts, detection_class, creation_datetime from jamcam.video_stats_v2 where camera_id = '"
            + id + '.mp4'
            + "' and video_upload_datetime > (select max(video_upload_datetime) from jamcam.video_stats_v2) - interval '12 hours';"
        )

        counts = {"truck": [], "person": [], "car": [], "motorbike": [], "bus": []}

        # for loops go brrrr...
        rows = [
            {column: value for column, value in rowproxy.items()} for rowproxy in res
        ]
        dates = set()

        for row in rows:
            dates.add(row["creation_datetime"])

        for date in list(dates):
            for type in counts:
                counts[type].append(0)
                for row in rows:
                    if row["creation_datetime"] == date and type == row['detection_class']:
                        counts[type][-1] = row[
                            "counts"
                        ]  # if row['counts'] is not None else counts[type].append(0)

        return {"dates": list(dates), "counts": counts}


class CamsSnapshot(APIQueryMixin):
    def query(self, session, type):
        """
        Return the result of the database view of the most recent
        """
        try:
            if type == "people":
                res = session.execute("select * from jamcam.sum_counts_last_hour_people")
            elif type == "cars":
                res = session.execute("select * from jamcam.sum_counts_last_hour_cars")
            elif type == "buses":
                res = session.execute("select * from jamcam.sum_counts_last_hour_buses")
            elif type == "trucks":
                res = session.execute("select * from jamcam.sum_counts_last_hour_trucks")
            elif type == "motorbikes":
                res = session.execute("select * from jamcam.sum_counts_last_hour_motorbikes")
            else:
                res = session.execute("select * from jamcam.sum_counts_last_hour")
            snapshot = {"camera_id": [], "sum_counts": []}
            for r in res:
                snapshot["camera_id"].append(r["camera_id"])
                snapshot["sum_counts"].append(r["sum_counts"])
            return json.dumps(snapshot)

        except ProgrammingError as error:
            if "psycopg2.errors.UndefinedTable" in str(error):
                print("Cam materialised views are not defined")
                raise

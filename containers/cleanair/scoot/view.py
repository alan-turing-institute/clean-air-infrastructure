
from sqlalchemy.exc import OperationalError
from .query import ScootQuery
from ..databases import DBWriter

class ScootView(ScootQuery):
    """
    Views for scoot analysis.
    """

    def create_borough_view(self, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00", view_name="borough_view"):
        """
        Create a view that stores all the borough aggregated stats for the given daterange.
        """
        command = """
            CREATE MATERIALIZED VIEW {name}
            AS {query}
            WITH DATA;
        """.format(
            name=view_name,
            query=self.agg_borough_df(
                start_datetime=start_datetime, end_datetime=end_datetime, return_sql=True
            )
        )

        with self.dbcnxn.engine.connect() as cnxn:
            try:
                cnxn.execute(command)
            except OperationalError:
                self.logger.warning(
                    "Database connection lost while running statement."
                )
            finally:
                cnxn.close()

    def create_detector_road_view(self, view_name="detector_road_view"):
        """
        Create a mapping from detectors to the closest road id.
        """
        command = """
            CREATE MATERIALIZED VIEW {name}
            AS {query}
            WITH DATA;
        """.format(
            name=view_name,
            query=self.detector_to_road_df(return_sql=True)
        )
    
    def refresh_view(self, view_name):
        command = "REFRESH MATERIALIZED VIEW {name};".format(name=view_name)
        with self.dbcnxn.engine.connect() as cnxn:
            try:
                cnxn.execute(command)
            except OperationalError:
                self.logger.warning(
                    "Database connection lost while running statement."
                )
            finally:
                cnxn.close()

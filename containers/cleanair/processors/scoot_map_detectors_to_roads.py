"""
Scoot feature extraction
"""
import time
from geoalchemy2.comparator import Comparator
import pandas as pd
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from ..databases import DBWriter
from ..databases.tables import MetaPoint, ScootDetector, OSHighway, ScootRoadMatch
from ..loggers import duration, get_logger, green
from ..mixins import DBQueryMixin


class ScootPerRoadDetectors(DBWriter, DBQueryMixin):
    """Map all road segments to their closest SCOOT detectors"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def match_to_roads(self, batch_size):
        """
        Match all road segments (OSHighway) with a SCOOT sensor (ScootDetector)

        Parameters
        ----------
        int batch_size
            An integer specifying how many unmatched roads to consider in a single batch

        Returns
        -------
        pandas.DataFrame
            A dataframe containing [road_toid, scoot_detector_n, distance_m] for each road-sensor association
        """
        while True:
            start_time = time.time()
            with self.dbcnxn.open_session() as session:
                # Get toids for all roads that have already been matched
                existing_road_toids = (
                    session.query(ScootRoadMatch.road_toid).distinct().all()
                )
                n_roads = session.query(OSHighway).count()

                # Stop here if we have matched all the roads
                self.logger.info(
                    "%i/%i roads have already been processed.",
                    len(existing_road_toids),
                    n_roads,
                )
                if len(existing_road_toids) >= n_roads:
                    break
                self.logger.info("Preparing to process the next %i roads.", batch_size)

                # Start by matching all detectors to the road they are on
                # NB. as a single road can have multiple detectors: the 12421 detectors represent 8160 distinct roads
                sq_roads_with_sensors = (
                    session.query(
                        OSHighway.toid.label("road_toid"),
                        ScootDetector.detector_n.label("scoot_detector_n"),
                        func.ST_Distance(
                            func.Geography(func.ST_Centroid(OSHighway.geom)),
                            func.Geography(MetaPoint.location),
                        ).label("distance_m"),
                    )
                    .join(ScootDetector, OSHighway.toid == ScootDetector.toid)
                    .join(MetaPoint)
                    .filter(OSHighway.toid.notin_(existing_road_toids))
                    .subquery()
                )

                # Load all roads that do not have sensors on them (limiting to batch size)
                sq_unmatched_roads = (
                    session.query(
                        OSHighway.toid.label("road_toid"),
                        OSHighway.geom.label("road_geom"),
                    )
                    .outerjoin(ScootDetector, OSHighway.toid == ScootDetector.toid)
                    .filter(ScootDetector.toid.is_(None))
                    .filter(OSHighway.toid.notin_(existing_road_toids))
                    .limit(batch_size)
                    .subquery()
                )

                # Get positions of all SCOOT sensors
                sq_scoot_sensors = (
                    session.query(
                        MetaPoint.location,
                        ScootDetector.toid.label("scoot_toid"),
                        ScootDetector.detector_n.label("scoot_detector_n"),
                    )
                    .join(ScootDetector)
                    .filter(MetaPoint.source == "scoot")
                    .subquery()
                )

                # Define a lateral query that can get the five closest sensors for a given road segment
                lateral_top5_by_distance = (
                    session.query(
                        sq_unmatched_roads.c.road_toid.label("lateral_road_toid"),
                        sq_scoot_sensors.c.scoot_detector_n.label(
                            "lateral_scoot_detector_n"
                        ),
                        func.ST_Distance(
                            func.Geography(
                                func.ST_Centroid(sq_unmatched_roads.c.road_geom)
                            ),
                            func.Geography(sq_scoot_sensors.c.location),
                        ).label("distance_m"),
                    )
                    .order_by(
                        # This uses the PostGIS <-> operator which performs an index-based nearest neighbour search
                        Comparator.distance_centroid(
                            sq_unmatched_roads.c.road_geom, sq_scoot_sensors.c.location
                        )
                    )
                    .limit(5)
                    .subquery()
                    .lateral()
                )

                # For roads that do not have sensors on them, construct one row for each of of the five closest sensors
                q_roads_without_sensors = session.query(
                    sq_unmatched_roads.c.road_toid,
                    lateral_top5_by_distance.c.lateral_scoot_detector_n.label(
                        "scoot_detector_n"
                    ),
                    lateral_top5_by_distance.c.distance_m,
                )

                # Combine the two road lists and read them into a local dataframe
                q_combined = session.query(sq_roads_with_sensors).union_all(
                    q_roads_without_sensors
                )
                df_matches = pd.read_sql(
                    q_combined.statement, q_combined.session.bind
                ).rename(
                    columns={
                        "anon_1_scoot_detector_n": "detector_n",
                        "anon_1_road_toid": "road_toid",
                        "anon_1_distance_m": "distance_m",
                    }
                )

                # Construct the weight column. The weight for each sensor is d / sum_0^n (d)
                df_matches["weight"] = (
                    df_matches["distance_m"]
                    .groupby(df_matches["road_toid"])
                    .transform(lambda x: 1.0 / sum(x))
                )
                df_matches["weight"] = df_matches["distance_m"] * df_matches["weight"]
                self.logger.info(
                    "Generated weights for %s road-sensor associations",
                    green(df_matches.shape[0]),
                )

            self.logger.info(
                "Constructing matches for a batch of %i roads took %s",
                batch_size,
                duration(start_time, time.time()),
            )
            # Yield the dataframe for this batch. When there is no dataframe we break
            if not df_matches.shape[0]:
                break
            yield df_matches

    def update_remote_tables(self):
        """Update the database with SCOOT road matches."""
        self.logger.info("Uploading %s road matches...", green("SCOOT"))
        start_time = time.time()
        n_records = 0

        # Get batched road matches as data frames
        for road_match_df in self.match_to_roads(batch_size=10000):
            road_match_records = road_match_df.to_dict("records")

            # Insert road matches into the database
            if len(road_match_records) > 0:
                self.logger.info(
                    "Preparing to insert %s road matches into database",
                    green(len(road_match_records)),
                )

                # Open a session and insert the road matches
                start_session = time.time()
                with self.dbcnxn.open_session() as session:
                    try:
                        # Commit and override any existing records
                        self.commit_records(
                            session,
                            road_match_records,
                            on_conflict="overwrite",
                            table=ScootRoadMatch,
                        )
                        n_records += len(road_match_records)
                    except IntegrityError as error:
                        self.logger.error(
                            "Failed to add road matches to the database: %s",
                            type(error),
                        )
                        self.logger.error(str(error))
                        session.rollback()

                self.logger.info(
                    "Insertion took %s", duration(start_session, time.time())
                )

        # Summarise updates
        self.logger.info(
            "Committed %s road matches to table %s in %s",
            green(n_records),
            green(ScootRoadMatch.__tablename__),
            green(duration(start_time, time.time())),
        )

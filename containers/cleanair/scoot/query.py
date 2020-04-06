from ..databases import DBReader
from ..databases.tables import OSHighway, ScootReading, ScootDetector
import pandas as pd

class ScootQuery(DBReader):
    """
    Queries to run on the SCOOT DB.
    """
    
    def groupby_datetime_df(self, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        """
        Group by hour and return the average or sum of the column for that hour.
        """
        query = """
            SELECT measurement_start_utc, measurement_end_utc,
                SUM(n_vehicles_in_interval) AS sum_n_vehicles_in_interval,
                AVG(occupancy_percentage) as avg_occupancy_percentage,
                AVG(congestion_percentage) as avg_congestion_percentage,
                AVG(saturation_percentage) as avg_saturation_percentage,
                SUM(flow_raw_count) as sum_flow_raw_count,
                SUM(occupancy_raw_count) as sum_occupancy_raw_count,
                SUM(congestion_raw_count) as sum_congestion_raw_count,
                SUM(saturation_raw_count) as sum_saturation_raw_count
            FROM dynamic_data.scoot_reading
            WHERE measurement_start_utc >= '{start}' AND measurement_start_utc < '{end}'
            group by measurement_start_utc, measurement_end_utc
            order by measurement_start_utc;
        """.format(start=start_datetime, end=end_datetime)
    
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def detector_to_road_df(self, return_sql=True, radius=50):
        """
        Get a mapping from each detector id to the id of the nearest road.

        Parameters
        ___

        return_sql : bool, optional
            If true, returns a string of sql instead of executing query.

        radius : float, optional
            Radius of intersection disk for detectors in meters.
        """
        query = """
            SELECT
                detector_id,
                toid AS road_id,
                name as borough_name,
                ST_Distance(st_transform(scoot.location, 27700), st_transform(road.geom, 27700)) as distance_to_road,
                lon,
                lat,
                scoot.location,
                startnode,
                endnode,
                road_classification,
                route_hierarchy,
                form_of_way,
                primary_route,
                directionality,
                length,
                road.geom
            FROM
                ({detector_borough}) as scoot
            JOIN
                static_data.oshighway_roadlink as road ON ST_Intersects(
                    st_transform(road.geom, 27700), ST_Expand(st_transform(scoot.location, 27700), {radius})
                )
        """.format(
            detector_borough=self.detector_borough_join_query(),
            radius=radius
        )
        if return_sql:
            return query
        query += ";"
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df
      
    def groupby_sensor_df(self, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        query = """
            select 
                ST_AsText(boundary.geom),
                boundary.name,
                measurement_start_utc,
                avg_n_vehicles_in_interval,
                total_n_vehicles_in_interval,
                avg_occupancy_percentage,
                avg_congestion_percentage,
                avg_saturation
            from 
                (
                    with scoot as (
                        SELECT detector_id, interest_points.meta_point."location" as location, 
                            ST_X(interest_points.meta_point."location") as "lon",
                            ST_Y(interest_points.meta_point."location") as "lat",
                            measurement_start_utc, measurement_end_utc, n_vehicles_in_interval,
                            occupancy_percentage, congestion_percentage, saturation_percentage as "saturation"
                        FROM dynamic_data.scoot_reading 
                        join interest_points.scoot_detector on detector_id = interest_points.scoot_detector.detector_n 
                        join interest_points.meta_point on id = interest_points.scoot_detector.point_id
                        where measurement_start_utc >= '{start}' AND measurement_start_utc < '{end}' and interest_points.meta_point."source" = 'scoot'
                    )
                    select name, measurement_start_utc,
                        sum(n_vehicles_in_interval) as total_n_vehicles_in_interval,
                        avg(n_vehicles_in_interval) as avg_n_vehicles_in_interval,
                        avg(occupancy_percentage) as avg_occupancy_percentage,
                        avg(congestion_percentage) as avg_congestion_percentage,
                        avg(saturation) as avg_saturation
                    from static_data.london_boundary, scoot
                    where ST_Intersects(geom, location)
                    group by name, measurement_start_utc
                ) as scoot,
                static_data.london_boundary as boundary
            where
                boundary.name=scoot.name;

        """.format(start=start_datetime, end=end_datetime)
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def detector_borough_join_query(self):
        return  """
            SELECT 
                scoot.detector_n as detector_id,
                static_data.london_boundary.name,
                ST_X(interest_points.meta_point."location") as "lon",
                ST_Y(interest_points.meta_point."location") as "lat",
                interest_points.meta_point.location as location,
                ST_ASTEXT(static_data.london_boundary.geom) AS geom
            from
                static_data.london_boundary,
                interest_points.scoot_detector as scoot
            JOIN
                interest_points.meta_point ON interest_points.meta_point.id = scoot.point_id
            where
                ST_Intersects(static_data.london_boundary.geom, interest_points.meta_point.location)
            """

    def detector_borough_join_df(self):
        """
        Get a dataframe of detector ids and the borough they lie in.
        """
        query = self.detector_borough_join_query()
        query += ";"
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def agg_borough_df(self, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00", return_sql=False):
        inner_query = self.detector_borough_join_query()
        query = """
            SELECT
                measurement_start_utc,
                measurement_end_utc,
                name,
                SUM(n_vehicles_in_interval) AS sum_n_vehicles_in_interval,
                AVG(n_vehicles_in_interval) AS avg_n_vehicles_in_interval,
                AVG(occupancy_percentage) as avg_occupancy_percentage,
                AVG(congestion_percentage) as avg_congestion_percentage,
                AVG(saturation_percentage) as avg_saturation_percentage,
                SUM(flow_raw_count) as sum_flow_raw_count,
                SUM(occupancy_raw_count) as sum_occupancy_raw_count,
                SUM(congestion_raw_count) as sum_congestion_raw_count,
                SUM(saturation_raw_count) as sum_saturation_raw_count,
                geom
            FROM dynamic_data.scoot_reading AS reading
            JOIN ({inner_query}) AS borough_detector ON borough_detector.detector_id = reading.detector_id
            WHERE measurement_start_utc >= '{start}' AND measurement_start_utc < '{end}'
            GROUP BY borough_detector.name, measurement_start_utc, measurement_end_utc, geom
        """.format(
            inner_query=inner_query,
            start=start_datetime,
            end=end_datetime
        )
        if return_sql:
            return query
        query += ";"
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df
        
    def get_all_readings(self, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        """
        Get every reading for every SCOOT detector + the lat and lon of the sensor.
        """
        query = """
            SELECT detector_id, ST_X(interest_points.meta_point."location") as "lon",
                ST_Y(interest_points.meta_point."location") as "lat",
                measurement_start_utc, measurement_end_utc,
                n_vehicles_in_interval, occupancy_percentage,
                congestion_percentage, saturation_percentage as "saturation"
            FROM dynamic_data.scoot_reading 
            JOIN interest_points.scoot_detector on detector_id = interest_points.scoot_detector.detector_n 
            JOIN interest_points.meta_point on id = interest_points.scoot_detector.point_id
            WHERE measurement_start_utc >= '{start}' AND measurement_start_utc < '{end}'
        """.format(start=start_datetime, end=end_datetime)
        
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def get_readings_for_hour(self, hour):
        """
        Get the data for every scoot sensor for the given hour.
        """
        query = """
            SELECT detector_id, ST_X(interest_points.meta_point."location") as "lon",
                ST_Y(interest_points.meta_point."location") as "lat",
                measurement_start_utc, measurement_end_utc,
                n_vehicles_in_interval, occupancy_percentage,
                congestion_percentage, saturation_percentage as "saturation"
            FROM dynamic_data.scoot_reading 
            JOIN interest_points.scoot_detector on detector_id = interest_points.scoot_detector.detector_n 
            JOIN interest_points.meta_point on id = interest_points.scoot_detector.point_id
            WHERE measurement_start_utc = '{hour}';
        """.format(hour=hour)
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def get_random_detectors(self, p, return_sql=False):
        """
        Randomly get p% of the scoot detectors.
        """
        query = """
            SELECT * FROM interest_points.scoot_detector
            TABLESAMPLE SYSTEM ({p})
        """.format(p=p)
        if return_sql:
            return query
        query += ";"
        with self.dbcnxn.open_session() as session:
            df = pd.read_sql(query, session.bind)
            return df

    def get_readings_for_subset(self, subset, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        """
        Get all readings for the subset of scoot sensors between the two datetimes.
        """
        with self.dbcnxn.open_session() as session:
            query = session.query(ScootReading)
            query = query.filter(ScootReading.measurement_start_utc >= start_datetime).filter(
                ScootReading.measurement_start_utc < end_datetime
            ).filter(
                ScootReading.detector_id.in_(subset)
            )
            return pd.read_sql(query.statement, query.session.bind)

    def get_road_network(self, only_central_boroughs=False, only_major_roads=True):
        """
        Return data for the road network.
        """

        if only_central_boroughs:
            raise NotImplementedError("Coming soon: return roads only for central boroughs.")

        with self.dbcnxn.open_session() as session:
            query = session.query(OSHighway)
            if only_major_roads:
                query = query.filter(OSHighway.road_classification.in_(["A Road", "B Road"]))
            return pd.read_sql(query.statement, query.session.bind)

    def get_readings_for_detector(self, detector_id, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        """
        Get all the readings for the given timerange for just one sensor.
        """
        with self.dbcnxn.open_session() as session:
            query = session.query(ScootReading)
            query.filter(ScootReading.detector_id == detector_id).filter(
                ScootReading.measurement_start_utc < end_datetime
            ).filter(
                ScootReading.measurement_start_utc >= start_datetime
            )
            return pd.read_sql(query.statement, query.session.bind)
            


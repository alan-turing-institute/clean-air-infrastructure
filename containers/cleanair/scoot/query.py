from ..databases import DBReader
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
      
    def groupby_sensor_df(self):
        query = """
            select 
                boundary.geom,
                boundary.name,
                measurement_start_utc,
                n_vehicles_in_interval,
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
                        where measurement_start_utc >= '2020-02-23' AND measurement_start_utc < '2020-02-25' and interest_points.meta_point."source" = 'scoot'
                    )
                    select name, measurement_start_utc, avg(n_vehicles_in_interval) as n_vehicles_in_interval,
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

        """
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

    def get_random_detectors(self, n):
        """
        Get n random scoot detectors.
        """
        raise NotImplementedError()

    def get_readings_for_subset(self, subset, start_datetime="2020-02-23 06:00:00", end_datetime="2020-02-23 18:00:00"):
        """
        Get all readings for the subset of scoot sensors between the two datetimes.
        """
        raise NotImplementedError()

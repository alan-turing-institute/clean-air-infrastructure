with scoot as (SELECT detector_id, interest_points.meta_point."location" as location, ST_X(interest_points.meta_point."location") as "lon", ST_Y(interest_points.meta_point."location") as "lat", measurement_start_utc, measurement_end_utc, n_vehicles_in_interval, occupancy_percentage, congestion_percentage, saturation_percentage as "saturation"
FROM dynamic_data.scoot_reading join interest_points.scoot_detector on detector_id = interest_points.scoot_detector.detector_n 
join interest_points.meta_point on id = interest_points.scoot_detector.point_id
where measurement_start_utc >= '2020-02-23' and interest_points.meta_point."source" = 'scoot')
select name, measurement_start_utc, avg(n_vehicles_in_interval) as n_vehicles_in_interval, avg(occupancy_percentage) as avg_occupancy_percentage, avg(congestion_percentage) as avg_congestion_percentage, avg(saturation) as avg_saturation
from static_data.london_boundary, scoot
where ST_Intersects(geom, location)
group by name, measurement_start_utc

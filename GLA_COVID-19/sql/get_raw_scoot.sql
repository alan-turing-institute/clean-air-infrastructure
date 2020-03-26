SELECT detector_id, ST_X(interest_points.meta_point."location") as "lon", ST_Y(interest_points.meta_point."location") as "lat", measurement_start_utc, measurement_end_utc, n_vehicles_in_interval, occupancy_percentage, congestion_percentage, saturation_percentage as "saturation"
FROM dynamic_data.scoot_reading join interest_points.scoot_detector on detector_id = interest_points.scoot_detector.detector_n 
join interest_points.meta_point on id = interest_points.scoot_detector.point_id
where measurement_start_utc > '2020-02-01'
order by detector_id, measurement_start_utc 
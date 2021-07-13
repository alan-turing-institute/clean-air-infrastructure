SELECT point_id, measurement_start_utc, "NO2_mean", "NO2_var", ST_AsGeoJSON(interest_points.meta_point.location) as location, interest_points.meta_point.source
FROM air_quality_modelling.air_quality_result
JOIN interest_points.meta_point on interest_points.meta_point.id = point_id
WHERE instance_id = 'd7c08a980c54762fb7f9aa5e2cc069856230648d80e0a70bf9d3949027e88695'
LIMIT 10
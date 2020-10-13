SELECT point_id, measurement_start_utc, feature_name, value_1000, value_500, value_200, value_100, value_10,  ST_AsGeoJSON(interest_points.meta_point.location) as location, interest_points.meta_point.source
FROM model_features.dynamic_feature
JOIN interest_points.meta_point on interest_points.meta_point.id = point_id
WHERE model_features.dynamic_feature.measurement_start_utc >= '2020-10-13T00:00:00' 
AND model_features.dynamic_feature.measurement_start_utc < '2020-10-14T00:00:00'
ORDER BY point_id ASC, feature_name ASC, measurement_start_utc ASC  LIMIT 100

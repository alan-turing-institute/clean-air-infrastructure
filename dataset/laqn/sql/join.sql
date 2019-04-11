drop table if exists orca.laqn_hourly_data_with_geom;
select 
   site.id as site_id,
   site.sitecode,
   data.date,
   site.sitetype,
   site.latitude,
   site.longitude,
   data.no2,
   data.o3,
   data.pm10_raw,
   data.pm10,
   data.pm25,
   site.geom
into
   orca.laqn_hourly_data_with_geom
from
   orca.laqn_hourly_data as data,
   orca.laqn_sites as site
where
   data.site = site.sitecode and
   site.latitude is not NULL and 
   site.longitude is not NULL;

create index on orca.laqn_hourly_data_with_geom (site_id, date);

copy (
   select 
      site.sitecode,
      data.date,
      site.sitetype,
      site.latitude,
      site.longitude,
      data.no2,
      data.o3,
      data.pm10_raw,
      data.pm10,
      data.pm25
   from
      orca.laqn_hourly_data as data,
      orca.laqn_sites as site
   where
      data.site = site.sitecode and
      site.latitude is not NULL and 
      site.longitude is not NULL  
   order by 
      (site.sitecode, data.date)
) to '/Users/ohamelijnck/Documents/london_air/covariates/LondonairDownloader/laqn_with_lat_lon.csv' DELIMITER ',' CSV HEADER;


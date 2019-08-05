drop table if exists orca.aqe_data_with_site;
drop table if exists orca.aqe_data;

create table  orca.aqe_data (
   site_code varchar not null,
   datetime timestamp not null,
   no2 double precision,
   pm10 double precision,
   pm25 double precision,
   primary key (site_code, datetime)
);

\copy orca.aqe_data FROM 'data.csv' HEADER DELIMITER ',' CSV

select
   sites.id as site_id,
   data.*,
   sites.geom
into
  orca.aqe_data_with_site 
from
   orca.aqe_data as data,
   orca.aqe_sites as sites
where
   data.site_code = sites.SiteCode;

CREATE INDEX aqe_data_with_site_gix ON orca.aqe_data_with_site USING GIST(geom);

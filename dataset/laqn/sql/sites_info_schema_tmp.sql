DROP TABLE IF EXISTS orca.sites;
DROP TABLE IF EXISTS orca.laqn_sites_tmp;
DROP TABLE IF EXISTS orca.laqn_sites;

CREATE TABLE orca.laqn_sites_tmp (
   SiteCode VARCHAR(3) NOT NULL,
   la_id integer NOT NULL,
   SiteType VARCHAR(20) NOT NULL,
   os_grid_x DOUBLE PRECISION,
   os_grid_y DOUBLE PRECISION,
   Latitude DOUBLE PRECISION,
   Longitude DOUBLE PRECISION,
   DateOpened TIMESTAMP,
   DateClosed TIMESTAMP, -- if NULL means that it hasn't closed yet
   PRIMARY KEY(SiteCode)
);

-- IMPORT DATA

COPY orca.laqn_sites_tmp FROM '/Users/ohamelijnck/Documents/london_air/covariates/LondonairDownloader/sites_info/site_info.csv' HEADER DELIMITER ';' CSV;

SELECT AddGeometryColumn('orca', 'laqn_sites_tmp', 'geom', 4326, 'POINT', 2);
UPDATE orca.laqn_sites_tmp SET geom = ST_SetSRID(ST_MakePoint(Longitude, Latitude), 4326);

-- select ones which lie in the london boundary and have data

select
   sites.SiteCode,
   sites.la_id,
   sites.SiteType,
   sites.os_grid_x,
   sites.os_grid_y,
   sites.Latitude,
   sites.Longitude,
   sites.DateOpened,
   sites.DateClosed,
   sites.geom
into 
   orca.laqn_sites 
from
   orca.laqn_sites_tmp as sites,
   orca.london_boundary as boundary,
   (select distinct(site) as code from orca.laqn_hourly_data) as codes
where
   sites.Latitude is not null and 
   sites.Longitude is not null and
   sites.SiteCode = codes.code and
   ST_Intersects(sites.geom, boundary.geom);

CREATE INDEX laqn_sites_gix ON orca.laqn_sites USING GIST(geom);
ALTER TABLE orca.laqn_sites ADD COLUMN id SERIAL PRIMARY KEY;
drop table orca.laqn_sites_tmp;



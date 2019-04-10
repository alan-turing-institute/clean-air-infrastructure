DROP TABLE IF EXISTS orca.sites CASCADE;
DROP TABLE IF EXISTS orca.laqn_sites CASCADE;

CREATE TABLE orca.laqn_sites (
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

COPY orca.laqn_sites FROM <SITE_INFO_CSV> HEADER DELIMITER ';' CSV;

SELECT AddGeometryColumn('orca', 'laqn_sites', 'geom', 4326, 'POINT', 2);
UPDATE orca.laqn_sites SET geom = ST_SetSRID(ST_MakePoint(Longitude, Latitude), 4326);
CREATE INDEX laqn_sites_gix ON orca.laqn_sites USING GIST(geom);




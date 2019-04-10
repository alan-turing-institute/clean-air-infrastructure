drop table if exists orca.aqe_sites;
CREATE TABLE orca.aqe_sites (
	SiteCode VARCHAR NOT NULL,
	SiteName VARCHAR NOT NULL,
	SiteType varchar NOT NULL,
	DateOpened date NOT NULL,
	lat double precision NOT NULL,
	lon double precision NOT NULL
);


\copy orca.aqe_sites FROM 'sites.csv' HEADER DELIMITER ',' CSV

SELECT AddGeometryColumn('orca', 'aqe_sites', 'geom', 4326, 'POINT', 2);
UPDATE orca.aqe_sites SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);
CREATE INDEX aqe_sites_gix ON orca.aqe_sites USING GIST(geom);

ALTER TABLE orca.aqe_sites ADD COLUMN id SERIAL PRIMARY KEY;

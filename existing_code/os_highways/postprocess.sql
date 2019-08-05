-- convert geom from 27700 to 4326
ALTER TABLE orca.os_highways_links ALTER COLUMN geom TYPE geometry(MultiLineString,4326) USING ST_Transform(geom,4326);
CREATE INDEX os_highways_links_gix ON orca.os_highways_links USING GIST(geom);

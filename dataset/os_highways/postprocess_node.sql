-- convert geom from 27700 to 4326
ALTER TABLE orca.os_highways_nodes  ALTER COLUMN geom TYPE geometry(Point,4326) USING ST_Transform(geom,4326);
CREATE INDEX os_highways_nodes_gix ON orca.os_highways_nodes USING GIST(geom);


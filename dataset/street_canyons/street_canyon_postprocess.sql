ALTER TABLE orca.street_canyons
  ALTER COLUMN geom TYPE geometry(MULTILINESTRING, 4326)
    USING ST_SetSRID(ST_Transform(geom,4326), 4326);

create index street_canyon_gix on orca.street_canyons using GIST(geom);

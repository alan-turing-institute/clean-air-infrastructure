drop table if exists hexgrid_tmp;
CREATE TABLE hexgrid_tmp (
  col_id integer,
  row_id integer,
  hex_id integer,
  area float,
  geom geometry,
  point_id varchar
);

COPY hexgrid_tmp FROM '/Users/ohamelijnck/Documents/projects/clean_air_repo/clean-air-infrastructure/run_model/visualisation/hexgrid.csv' DELIMITER ',' CSV HEADER;

COPY (
   select 
      col_id,
      row_id,
      hex_id,
      area,
      point_id,
      ST_AsText((st_dump(geom)).geom) as geom
   from hexgrid_tmp
) TO  '/Users/ohamelijnck/Documents/projects/clean_air_repo/clean-air-infrastructure/run_model/visualisation/hexgrid_polygon.csv' DELIMITER ',' CSV HEADER;


drop table if exists hexgrid_tmp;

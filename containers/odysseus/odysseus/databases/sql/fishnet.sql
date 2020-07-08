CREATE TYPE grid_cell as (              -- a record in the returned query below
	row INTEGER,
	col INTEGER,
	geom GEOGRAPHY
);

-- create a grid that contains a polygon
-- you can rotate the grid, pass different coordinate systems
-- and change the size of the grid cells
CREATE OR REPLACE FUNCTION ST_FishnetOverPolygon(
    bound_polygon geometry,             -- polygon to draw fishnet over
    grid_step integer,                  -- size of grid cell in meters
    metric_srid integer := 4326,        -- spatial reference id
    rotation DOUBLE PRECISION := 0      -- the rotation of the grid in degrees
)
RETURNS SETOF grid_cell                 -- return a set of grid cells
AS $$
BEGIN
	RETURN QUERY 
    SELECT
        i as row,                       -- row id
        j as col,                       -- column id
        ST_CreateGridSquare(            -- geograph of the grid cell
            ST_Project(                 -- translate in the y axis
                ST_Project(             -- translate in the x axis
                    cell,
                    j * grid_step,
                    radians(rotation + 90)
                ),
                i * grid_step,
                radians(rotation)
            ),
            grid_step,
            rotation
        ) AS geom
    FROM generate_series(0, 16) AS i,   -- currently creates a 16 by 16 grid
        generate_series(0, 16) AS j,
        (SELECT ST_MakePoint(
            ST_XMin(ST_Transform(bound_polygon, metric_srid)),
            ST_YMin(ST_Transform(bound_polygon, metric_srid))
        ) AS cell) AS foo;
END
$$ LANGUAGE 'plpgsql';
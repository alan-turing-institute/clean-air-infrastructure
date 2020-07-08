CREATE OR REPLACE FUNCTION ST_CreateGridSquare(
    bottom_left GEOGRAPHY,              -- bottom left corner of the grid cell
    size INTEGER,                       -- length of each edge in meters
    rotation DOUBLE PRECISION           -- rotate the grid cell in degrees
)
RETURNS GEOGRAPHY AS
$grid_square$
DECLARE
    top_left GEOMETRY;
    top_right GEOMETRY;
    bottom_right GEOMETRY;
BEGIN
    top_left := ST_Project(bottom_left, size, radians(rotation));
    top_right := ST_Project(top_left, size, radians(rotation + 90));
    bottom_right := ST_Project(bottom_left, size, radians(rotation + 90));
    RETURN ST_MakePolygon(ST_MakeLine(ARRAY[    -- make a polygon from a linestring
        bottom_left, top_left, top_right, bottom_right, bottom_left
    ]::GEOMETRY[]));
END;
$grid_square$
LANGUAGE 'plpgsql';
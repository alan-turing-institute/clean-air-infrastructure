"""Create grids over London."""

from shapely.geometry.base import BaseGeometry
from cleanair.decorators import db_query

@db_query
def grid_over_geom(geom: BaseGeometry, grid_step: int = 1000, rotation: float = 0, srid: int = 4326):
    """Create a grid that contains the geometry.

    Args:
        geom: The geometry to cover with a grid.
        grid_step: The length of each grid square in meters.
        rotation: Rotation of the grid (in degrees).
        srid: Spatial reference system ID.
    
    Returns:
        Database query. Set output_type="df" to get a dataframe.
    """
    


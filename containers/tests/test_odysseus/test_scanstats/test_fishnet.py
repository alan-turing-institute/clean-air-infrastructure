"""Test that a grid is created over polygons and boroughs."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapely.geometry import Polygon

def test_fishnet_over_square(grid, square) -> None:
    """Test the fishnet is cast correctly over a square."""
    fishnet_df = grid.fishnet_over_geom(square, output_type="df")
    assert len(fishnet_df) > 0

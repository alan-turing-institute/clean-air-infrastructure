"""Test that a grid is created over polygons and boroughs."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapely.geometry import Polygon

def test_fishnet_over_square(grid, square) -> None:
    """Test the fishnet is cast correctly over a square."""
    grid_res = 4
    fishnet_df = grid.fishnet_over_geom(square, grid_res, output_type="df")
    assert len(fishnet_df) > grid_res ** 2
    assert 0 < fishnet_df["row"] < grid_res + 1
    assert 0 < fishnet_df["col"] < grid_res + 1

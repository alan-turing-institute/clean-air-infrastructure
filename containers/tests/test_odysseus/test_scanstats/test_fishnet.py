"""Test that a grid is created over polygons and boroughs."""

from typing import TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    from shapely.geometry import Polygon

def test_fishnet_over_square(grid, square) -> None:
    """Test the fishnet is cast correctly over a square."""
    grid_res = 4
    fishnet_df = grid.st_fishnet(square, grid_res, output_type="df")
    print(fishnet_df)
    assert isinstance(fishnet_df, pd.DataFrame)
    assert "row" in fishnet_df.columns
    assert "col" in fishnet_df.columns
    assert "geom" in fishnet_df.columns
    assert len(fishnet_df) == grid_res ** 2
    assert 0 < fishnet_df["row"].all() < grid_res + 1
    assert 0 < fishnet_df["col"].all() < grid_res + 1

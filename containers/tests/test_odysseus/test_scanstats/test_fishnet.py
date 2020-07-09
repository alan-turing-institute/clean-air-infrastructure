"""Test that a grid is created over polygons and boroughs."""

from __future__ import annotations
from typing import TYPE_CHECKING
from cleanair.databases.tables import LondonBoundary

if TYPE_CHECKING:
    import pandas as pd
    from shapely.geometry import Polygon

def fishnet_checks(fishnet_df: pd.DataFrame, geom: Polygon, grid_resolution: int):
    """Run checks that a fishnet has been cast correctly on the geometry."""
    assert "row" in fishnet_df.columns
    assert "col" in fishnet_df.columns
    assert "geom" in fishnet_df.columns
    assert len(fishnet_df) == grid_resolution ** 2
    assert 0 < fishnet_df["row"].all() < grid_resolution + 1
    assert 0 < fishnet_df["col"].all() < grid_resolution + 1

def test_fishnet_over_square(grid, square) -> None:
    """Test the fishnet is cast correctly over a square."""
    grid_res = 4
    fishnet_df = grid.st_fishnet(square, grid_res, output_type="df")
    print(fishnet_df)
    fishnet_checks(fishnet_df, square, grid_res)

def test_fishnet_over_borough(grid) -> None:
    """Test the fishnet is cast over the borough."""
    borough = "Westminster"
    grid_res = 8

    # get the borough geometry
    with grid.dbcnxn.open_session() as session:
        geom = session.query(LondonBoundary.geom).filter(LondonBoundary.name == borough).one()

    fishnet_df = grid.fishnet_over_borough(borough, grid_res, output_type="df")
    fishnet_checks(fishnet_df, geom, grid_res)

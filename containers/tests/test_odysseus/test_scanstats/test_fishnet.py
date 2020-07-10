"""Test that a grid is created over polygons and boroughs."""

from __future__ import annotations
from typing import TYPE_CHECKING, Union
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon
from shapely import wkb
from cleanair.databases.tables import LondonBoundary


if TYPE_CHECKING:
    import pandas as pd


def fishnet_checks(
    fishnet_df: pd.DataFrame, geom: Union[Polygon, MultiPolygon], grid_resolution: int
):
    """Run checks that a fishnet has been cast correctly on the geometry."""
    assert "row" in fishnet_df.columns
    assert "col" in fishnet_df.columns
    assert "geom" in fishnet_df.columns
    assert len(fishnet_df) == grid_resolution ** 2
    assert 0 < fishnet_df["row"].all() < grid_resolution + 1
    assert 0 < fishnet_df["col"].all() < grid_resolution + 1

    # create a geoseries
    nodes = []
    fishnet_df["geom"].apply(
        lambda x: nodes.extend(
            [Point(y) for y in wkb.loads(x, hex=True).exterior.coords]
        )
    )
    multi_points = MultiPoint(nodes)
    assert len(nodes) == grid_resolution ** 2 * 5
    assert multi_points.convex_hull.buffer(1e-10).contains(geom)


def test_fishnet_over_square(grid, square) -> None:
    """Test the fishnet is cast correctly over a square."""
    grid_res = 4
    fishnet_df = grid.st_fishnet(
        from_shape(square, srid=4326), grid_res, output_type="df"
    )
    print(fishnet_df)
    fishnet_checks(fishnet_df, square, grid_res)


def test_fishnet_over_borough(grid) -> None:
    """Test the fishnet is cast over the borough."""
    borough = "Westminster"
    grid_res = 8

    # get the borough geometry
    with grid.dbcnxn.open_session() as session:
        result = (
            session.query(LondonBoundary).filter(LondonBoundary.name == borough).one()
        )
        geom = to_shape(result.geom)
        assert isinstance(geom, MultiPolygon)

    print(grid.fishnet_over_borough(borough, grid_res, output_type="sql"))
    fishnet_df = grid.fishnet_over_borough(borough, grid_res, output_type="df")
    fishnet_checks(fishnet_df, geom, grid_res)

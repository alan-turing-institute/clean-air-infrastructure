"""Test database queries for the scoot scan stats."""

from __future__ import annotations
from typing import TYPE_CHECKING
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import to_shape
from shapely import wkb

if TYPE_CHECKING:
    from odysseus.scoot import ScanScoot

def test_scoot_fishnet(scan_scoot: ScanScoot) -> None:
    """Test that a fishnet is cast over a borough and detectors are mapped to grid squares."""
    detector_df = scan_scoot.scoot_fishnet("Westminster", output_type="df")
    print(detector_df.columns)
    assert len(detector_df) > 0
    assert "geom" in detector_df.columns
    assert "location" in detector_df.columns
    assert "col" in detector_df.columns
    assert "row" in detector_df.columns
    assert "detector_id" in detector_df.columns
    print(detector_df.dtypes)
    detector_df["geom"] = detector_df["geom"].apply(lambda x: wkb.loads(x, hex=True))
    print(type(detector_df.at[0, "location"]))
    detector_df["location"] = detector_df["location"].apply(to_shape)
    # assert detector_df.dtypes["geom"] is Polygon
    assert isinstance(detector_df.at[0, "location"], Point)
    assert isinstance(detector_df.at[0, "geom"], Polygon)
    assert detector_df.apply(lambda x: x["geom"].contains(x["location"]), axis=1).all()

"""Test database queries for the scoot scan stats."""

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from shapely.geometry import Point, Polygon
from shapely import wkb
from geoalchemy2.shape import to_shape


if TYPE_CHECKING:
    from odysseus.scoot import ScanScoot


# def test_scoot_fishnet(scan_scoot: ScanScoot) -> None:
#     """Test that a fishnet is cast over a borough and detectors are mapped to grid squares."""
#     # create a fishnet over Westminster and map detectors to grid squares
#     detector_df = scan_scoot.scoot_fishnet("Westminster", output_type="df")

#     # check that the dataframe is not empty
#     assert len(detector_df) > 0

#     # check each of the columns is returned
#     assert "geom" in detector_df.columns
#     assert "location" in detector_df.columns
#     assert "col" in detector_df.columns
#     assert "row" in detector_df.columns
#     assert "detector_id" in detector_df.columns

#     # create shapely objects from the WKB string/object
#     detector_df["geom"] = detector_df["geom"].apply(lambda x: wkb.loads(x, hex=True))
#     detector_df["location"] = detector_df["location"].apply(to_shape)

#     # check the convertion to type is correct
#     assert isinstance(detector_df.at[0, "location"], Point)
#     assert isinstance(detector_df.at[0, "geom"], Polygon)

#     # check each detector is contained by the grid square it has been mapped to
#     assert detector_df.apply(lambda x: x["geom"].contains(x["location"]), axis=1).all()


def test_scoot_fishnet_readings(scoot_writer, scan_scoot: ScanScoot) -> None:
    """Test that the scoot readings are mapped to a fishnet over a borough."""
    scoot_writer.update_remote_tables()
    readings = scan_scoot.scoot_fishnet_readings(
        borough="Westminster",
        start_time=scoot_writer.start,
        end_time=scoot_writer.upto,
        output_type="df",
    )
    nhours = (
        datetime.fromisoformat(scoot_writer.upto) - datetime.fromisoformat(scoot_writer.start)
    ).days * 24
    assert len(readings) == scoot_writer.limit * nhours

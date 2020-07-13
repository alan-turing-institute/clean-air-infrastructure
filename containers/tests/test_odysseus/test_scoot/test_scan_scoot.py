"""Test database queries for the scoot scan stats."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odysseus.scoot import ScanScoot

def test_scoot_fishnet(scan_scoot: ScanScoot) -> None:
    """Test that a fishnet is cast over a borough and detectors are mapped to grid squares."""
    detector_df = scan_scoot.scoot_fishnet("Westminster", output_type="df")
    print(detector_df.columns)
    assert len(detector_df) > 0
    assert "geom" in detector_df.columns
    assert "square_geom" in detector_df.columns
    assert "col" in detector_df.columns
    assert "row" in detector_df.columns
    assert "detector_id" in detector_df.columns

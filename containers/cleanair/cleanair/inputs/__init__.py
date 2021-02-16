"""
Module for input datasources
"""
from .aqe_writer import AQEWriter
from .laqn_writer import LAQNWriter
from .rectgrid_writer import RectGridWriter
from .scoot_writer import ScootWriter, ScootReader
from .static_writer import StaticWriter
from .satellite_writer import SatelliteWriter

__all__ = [
    "AQEWriter",
    "LAQNWriter",
    "RectGridWriter",
    "ScootWriter",
    "ScootReader",
    "StaticWriter",
    "SatelliteWriter",
]

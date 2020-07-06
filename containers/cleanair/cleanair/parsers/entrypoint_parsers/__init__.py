<<<<<<< HEAD
from .feature_processing_parsers import create_satellite_input_parser

__all__ = ["create_satellite_input_parser"]
=======
"""Entrypoint argument parsers"""
from .feature_processing_parsers import (
    create_satellite_input_parser,
    create_static_feature_parser,
)

__all__ = ["create_satellite_input_parser", "create_static_feature_parser"]
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843

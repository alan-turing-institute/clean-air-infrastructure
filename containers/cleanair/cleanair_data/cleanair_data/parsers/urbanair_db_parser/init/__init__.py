"""Initialising an app and databases."""

from .init_callback import init_callback
from .init_database import app

__all__ = ["app", "init_callback"]

"""Initialising an app and databases."""

from .init_app import init_app
from .main import app

__all__ = ["app", "init_app"]

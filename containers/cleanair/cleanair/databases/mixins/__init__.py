"""Mixins for databases and tables."""

from .instance_tables_mixin import (
    DataTableMixin,
    InstanceTableMixin,
    ModelTableMixin,
)

__all__ = [
    "DataConfigMixin",
    "InstanceTableMixin",
    "ModelTableMixin",
]

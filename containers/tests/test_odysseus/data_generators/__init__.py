"""Generating fake data."""

from .scoot_generator import (
    create_daily_readings_df,
    generate_discrete_timeseries,
    generate_scoot_df,
)

__all__ = [
    "create_daily_readings_df",
    "generate_discrete_timeseries",
    "generate_scoot_df",
]

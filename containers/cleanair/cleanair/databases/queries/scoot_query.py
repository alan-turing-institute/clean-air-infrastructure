"""Scoot query class"""

from ...mixins.query_mixins.scoot_query_mixin import ScootQueryMixin
from ..db_reader import DBReader


class ScootQuery(DBReader, ScootQueryMixin):
    """Scoot query class"""

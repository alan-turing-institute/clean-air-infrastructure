"""Download the hexgrid to a CSV file"""

from pathlib import Path
import typer

from cleanair.databases import DBReader
from cleanair.mixins.query_mixins.hexgrid_query_mixin import HexGridQueryMixin


class HexGridQuery(HexGridQueryMixin, DBReader):
    """Hexgrid query"""

def main(secretfile: Path):
    """Download hexgrid"""
    query = HexGridQuery(secretfile=secretfile)
    df = query.query_hexgrid(output_type="df")
    print(df.sample(5))

if __name__ == "__main__":
    typer.run(main)

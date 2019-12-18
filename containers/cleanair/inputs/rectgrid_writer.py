"""
Get data from the AQE network via the API
"""
import numpy as np
from sqlalchemy.schema import CreateSchema
from ..databases import DBWriter
from ..databases.tables import MetaPoint, RectGrid
from ..loggers import get_logger, green


class RectGridWriter(DBWriter):
    """Manage interactions with the RectGrid table on Azure"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Bounding box for London
        self.latitude_range = (51.30, 51.69)
        self.longitude_range = (-0.49, 0.32)

        # To get a square(ish) grid we note that a degree of longitude is cos(latitude) times a degree of latitude
        # For London this means that a degree of latitude is about 1.5 times larger than one of longitude
        # We therefore alter the step sizes accordingly
        self.latitude_step = 0.002
        self.longitude_step = 0.003

    def build_cell(self, latitude, longitude):
        """Build a rectangular cell around a given latitude and longitude"""
        return "SRID=4326;POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))".format(
            longitude - 0.5 * self.longitude_step, latitude - 0.5 * self.latitude_step,
            longitude - 0.5 * self.longitude_step, latitude + 0.5 * self.latitude_step,
            longitude + 0.5 * self.longitude_step, latitude + 0.5 * self.latitude_step,
            longitude + 0.5 * self.longitude_step, latitude - 0.5 * self.latitude_step,
            longitude - 0.5 * self.longitude_step, latitude - 0.5 * self.latitude_step,
        )

    def update_remote_tables(self):
        """Upload grid data"""
        self.logger.info("Calculating static %s positions...", green("rectgrid"))
        grid_cells = []
        for idx_lat, latitude in enumerate(np.arange(*self.latitude_range, self.latitude_step)):
            for idx_long, longitude in enumerate(np.arange(*self.longitude_range, self.longitude_step)):
                grid_cells.append({"row_id": idx_lat,
                                   "column_id": idx_long,
                                   "geom": self.build_cell(latitude, longitude),
                                   "point_id": MetaPoint.build_ewkt(latitude, longitude),
                                   })

        # Ensure that interest_points table exists
        if not self.dbcnxn.engine.dialect.has_schema(self.dbcnxn.engine, "datasources"):
            self.dbcnxn.engine.execute(CreateSchema("datasources"))
        RectGrid.__table__.create(self.dbcnxn.engine, checkfirst=True)

        # Upload data to the database
        self.logger.info("Starting static %s upload...", green("rectgrid"))
        with self.dbcnxn.open_session() as session:
            # Update the meta_points table and retrieve point IDs
            self.logger.info("Merging %i grid points into %s table...", len(grid_cells), green(MetaPoint.__tablename__))
            meta_points = [MetaPoint.build_entry("rectgrid", geometry=g["point_id"]) for g in grid_cells]
            self.commit_records(session, meta_points, flush=True)
            for grid_cell, meta_point in zip(grid_cells, meta_points):
                grid_cell["point_id"] = meta_point.id  # this will be None if the record was not inserted

            # Commit the grid cell records to the database
            grid_records = [RectGrid.build_entry(grid_cell) for grid_cell in grid_cells if grid_cell["point_id"]]
            self.logger.info("Adding %i new cells to %s table...", len(grid_records), green("rectgrid"))
            self.commit_records(session, grid_records)

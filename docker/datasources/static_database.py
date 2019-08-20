"""
Get data from the AQE network via the API
"""
import glob
import os
import subprocess
from contextlib import suppress
from .databases import Connector
from .loggers import get_logger


class StaticDatabase():
    # table_names = {
    #     "UKMap.gdb": "ukmap",
    #     "Canyons": "canyonslondon",
    #     "RoadLink": "os_highways_links",
    #     "HexGrid": "hex_grid",
    #     "LondonBoundary": "london_boundary"
    # }

    """Manage interactions with the static database on Azure"""
    def __init__(self, **kwargs):
        self.dbcnxn = Connector(**kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))
        self.data_directory = None

    def upload_static_files(self):
        # Static files will be in /data
        try:
            self.data_directory = os.listdir("/data")[0]
            self.logger.critical("data_directory: %s", self.data_directory)
        except FileNotFoundError:
            raise FileNotFoundError("Could not find any static files in /data. Did you mount this path?")

        # Ensure that that the table exists and get the connection string
        _ = self.dbcnxn.engine
        connection_string = \
            "host={host} port={port} dbname={db_name} user={username} password={password} sslmode={ssl_mode}".format(
                **self.dbcnxn.connection_info)

        # Add additional arguments if the input data contains shape files
        extra_args = []
        if glob.glob("/data/{}/*.shp".format(self.data_directory)):
            extra_args = ["-nlt", "PROMOTE_TO_MULTI",
                          "-lco", "precision=NO"]

        # Set table name if it exists
        with suppress(KeyError):
            # table_name = self.table_names[self.data_directory]
            # extra_args += ["-nln", table_name]
            extra_args += ["-nln", self.data_directory]

        # # Run ogr2ogr
        # subprocess.run(["ogr2ogr", "-overwrite", "-progress",
        #                 "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.data_directory),
        #                 "--config", "PG_USE_COPY", "YES",
        #                 "-t_srs", "EPSG:4326"] + extra_args)

    def configure_database(self):
        sql_code = None

        if self.data_directory == "UKMap.gdb":
            sql_code = """CREATE INDEX ukmap_4326_gix ON ukmap USING GIST(shape);"""
            self.logger.info("Configuring UKMap data...")

        elif self.data_directory == "Canyons":
            sql_code = """CREATE INDEX canyonslondon_4326_gix ON canyonslondon USING GIST(wkb_geometry);"""
            self.logger.info("Configuring Street Canyons data...")

        elif self.data_directory == "RoadLink":
            sql_code = """CREATE INDEX roadlink_4326_gix ON os_highways_links USING GIST(wkb_geometry);"""
            self.logger.info("Configuring RoadLink data...")

        elif self.data_directory == "HexGrid":
            sql_code = """CREATE INDEX hex_grid_gix ON hex_grid USING GIST(wkb_geometry);"""
            self.logger.info("Configuring HexGrid data...")

        if sql_code:
            self.logger.debug("Preparing to run the following SQL code: %s", sql_code)
            # with self.dbcnxn.engine.connect() as conn:
            #     conn.execute(sql_code)

"""
Get data from the AQE network via the API
"""
import glob
import os
import subprocess
from contextlib import suppress
from .databases import Connector
from .loggers import get_logger, green

class StaticDatabase():
    """Manage interactions with the static database on Azure"""
    def __init__(self, **kwargs):
        self.dbcnxn = Connector(**kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))
        self.data_directory = None

    def upload_static_files(self):
        # Static files will be in /data
        try:
            self.data_directory = os.listdir("/data")[0]
            self.logger.debug("data_directory: %s", self.data_directory)
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

        # Set table name
        with suppress(KeyError):
            extra_args += ["-nln", self.data_directory]

        # Run ogr2ogr
        self.logger.info("Uploading static GIS data to %s in %s",
                         green(self.data_directory), green(self.dbcnxn.connection_info["db_name"]))
        subprocess.run(["ogr2ogr", "-overwrite", "-progress",
                        "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.data_directory),
                        "--config", "PG_USE_COPY", "YES",
                        "-t_srs", "EPSG:4326"] + extra_args)

    def configure_database(self):
        sql_code = None

        if self.data_directory == "ukmap":
            sql_code = """CREATE INDEX ukmap_gix ON ukmap USING GIST(shape);"""
            self.logger.info("Configuring UKMap data...")

        elif self.data_directory == "canyonslondon":
            sql_code = """CREATE INDEX canyonslondon_gix ON canyonslondon USING GIST(wkb_geometry);"""
            self.logger.info("Configuring Street Canyons data...")

        elif self.data_directory == "oshighwayroadlink":
            sql_code = """CREATE INDEX oshighwayroadlink_gix ON oshighwayroadlink USING GIST(wkb_geometry);"""
            self.logger.info("Configuring RoadLink data...")

        elif self.data_directory == "glahexgrid":
            sql_code = """CREATE INDEX glahexgrid_gix ON glahexgrid USING GIST(wkb_geometry);"""
            self.logger.info("Configuring HexGrid data...")

        if sql_code:
            self.logger.info("Running SQL code: %s", green(sql_code))
            with self.dbcnxn.engine.connect() as conn:
                conn.execute(sql_code)

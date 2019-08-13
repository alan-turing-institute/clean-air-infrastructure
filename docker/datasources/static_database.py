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
    table_names = {
        "UKMap.gdb": "ukmap",
        "Canyons": "canyonslondon",
        "RoadLink": "roadlink",
    }

    """Manage interactions with the static database on Azure"""
    def __init__(self, **kwargs):
        self.dbcnxn = Connector(**kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))
        self.static_filename = None

    def upload_static_files(self):
        # Static files will be in /data
        try:
            self.static_filename = os.listdir("/data")[0]
        except FileNotFoundError:
            raise FileNotFoundError("Could not find any static files in /data. Did you mount this path?")

        # Ensure that that the table exists and get the connection string
        _ = self.dbcnxn.engine
        connection_string = \
            "host={host} port={port} dbname={db_name} user={username} password={password} sslmode={ssl_mode}".format(
                **self.dbcnxn.connection_info)

        # Add additional arguments if the input data contains shape files
        extra_args = []
        if glob.glob("data/{}/*.shp".format(self.static_filename)):
            extra_args = ["-nlt", "PROMOTE_TO_MULTI",
                          "-lco", "precision=NO"]

        # Set table name if it exists
        with suppress(KeyError):
            table_name = self.table_names[self.static_filename]
            extra_args += ["-nln", table_name]

        # Run ogr2ogr
        subprocess.run(["ogr2ogr", "-overwrite", "-progress",
                        "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.static_filename),
                        "--config", "PG_USE_COPY", "YES",
                        "-t_srs", "EPSG:4326"] + extra_args)

    def configure_database(self):
        sql_code = None

        if self.static_filename == "UKMap.gdb":
            # sql_code = """ALTER TABLE public.base_hb0_complete_merged RENAME TO ukmap;
            #               CREATE INDEX ukmap_4326_gix ON ukmap USING GIST(shape);"""
            sql_code = """CREATE INDEX ukmap_4326_gix ON ukmap USING GIST(shape);"""
            self.logger.info("Configuring UKMap data...")

        elif self.static_filename == "Canyons":
            # sql_code = """ALTER TABLE canyonslondon_erase RENAME TO canyonslondon;
            #               CREATE INDEX canyonslondon_4326_gix ON canyonslondon USING GIST(wkb_geometry);"""
            sql_code = """CREATE INDEX canyonslondon_4326_gix ON canyonslondon USING GIST(wkb_geometry);"""
            self.logger.info("Configuring Street Canyons data...")

        elif self.static_filename == "RoadLink":
            sql_code = """CREATE INDEX roadlink_4326_gix ON roadlink USING GIST(wkb_geometry);"""
            self.logger.info("Configuring RoadLink data...")

        if sql_code:
            self.logger.debug("Preparing to run the following SQL code: %s", sql_code)
            with self.dbcnxn.engine.connect() as conn:
                conn.execute(sql_code)


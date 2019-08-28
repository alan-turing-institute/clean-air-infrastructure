"""
Get data from the AQE network via the API
"""
import glob
import os
import subprocess
from .databases import Connector
from .loggers import get_logger, green


class StaticDatabase():
    """Manage interactions with the static database on Azure"""
    def __init__(self, **kwargs):
        self.dbcnxn = Connector(**kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))
        self.data_directory = None
        self.table_name = None

    def upload_static_files(self):
        """Upload static data to the inputs database"""
        # Look for static files in /data then set the file and table names
        try:
            self.data_directory = os.listdir("/data")[0]
            self.logger.debug("data_directory: %s", self.data_directory)
        except FileNotFoundError:
            raise FileNotFoundError("Could not find any static files in /data. Did you mount this path?")
        self.table_name = self.data_directory.replace(".gdb", "")

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

        # Run ogr2ogr
        self.logger.info("Uploading static data to table %s in %s",
                         green(self.table_name), green(self.dbcnxn.connection_info["db_name"]))
        subprocess.run(["ogr2ogr", "-overwrite", "-progress",
                        "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.data_directory),
                        "--config", "PG_USE_COPY", "YES",
                        "-t_srs", "EPSG:4326",
                        "-nln", self.table_name] + extra_args)

    def configure_tables(self):
        """Tidy up the databases by doing the following:

        Adding an index on the geometry column
        Dropping (some) duplicate rows
        Dropping duplicate/unnecessary columns
        Converting some column types
        Adding a primary key
        """
        self.logger.info("Configuring database table: %s", green(self.table_name))
        sql_code = None

        if self.data_directory == "canyonslondon":
            sql_code = """
            DROP INDEX IF EXISTS canyonslondon_gix;
            CREATE INDEX canyonslondon_gix ON canyonslondon USING GIST(wkb_geometry);
            ALTER TABLE canyonslondon
                DROP COLUMN ave_relhma,
                DROP COLUMN identifier,
                DROP COLUMN identifi_2,
                DROP COLUMN length,
                DROP COLUMN min_length,
                DROP COLUMN max_length,
                DROP COLUMN objectid_1,
                DROP COLUMN objectid_2,
                DROP COLUMN objectid,
                DROP COLUMN ogc_fid,
                DROP COLUMN shape_le_1,
                DROP COLUMN sum_length,
                DROP COLUMN sum_shape_;
            ALTER TABLE canyonslondon
                ALTER fictitious TYPE bool
                USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;
            ALTER TABLE canyonslondon ADD PRIMARY KEY (toid);
            """

        elif self.data_directory == "glahexgrid":
            sql_code = """
            DROP INDEX IF EXISTS glahexgrid_gix;
            CREATE INDEX glahexgrid_gix ON glahexgrid USING GIST(wkb_geometry);
            ALTER TABLE glahexgrid
                DROP COLUMN col_id,
                DROP COLUMN ogc_fid,
                DROP COLUMN row_id;
            ALTER TABLE glahexgrid ADD PRIMARY KEY (hex_id);
            """

        elif self.data_directory == "londonboundary":
            sql_code = """
            DROP INDEX IF EXISTS londonboundary_gix;
            CREATE INDEX londonboundary_gix ON londonboundary USING GIST(wkb_geometry);
            ALTER TABLE londonboundary
                DROP COLUMN ogc_fid,
                DROP COLUMN sub_2006,
                DROP COLUMN sub_2009;
            ALTER TABLE londonboundary
                ALTER ons_inner TYPE bool
                USING CASE WHEN ons_inner='F' THEN FALSE ELSE TRUE END;
            ALTER TABLE londonboundary ADD PRIMARY KEY (gss_code);
            """

        elif self.data_directory == "oshighwayroadlink":
            sql_code = """
            DROP INDEX IF EXISTS oshighwayroadlink_gix;
            CREATE INDEX oshighwayroadlink_gix ON oshighwayroadlink USING GIST(wkb_geometry);
            ALTER TABLE oshighwayroadlink
                DROP COLUMN cyclefacil,
                DROP COLUMN elevatio_1,
                DROP COLUMN elevationg,
                DROP COLUMN identifi_1,
                DROP COLUMN identifier,
                DROP COLUMN ogc_fid,
                DROP COLUMN roadstruct,
                DROP COLUMN roadwidtha,
                DROP COLUMN roadwidthm;
            ALTER TABLE oshighwayroadlink
                ALTER fictitious TYPE bool
                USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;
            ALTER TABLE oshighwayroadlink ADD PRIMARY KEY (toid);
            """

        elif self.data_directory == "scootdetectors":
            sql_code = """
            DROP INDEX IF EXISTS scootdetectors_gix;
            CREATE INDEX scootdetectors_gix ON scootdetectors USING GIST(wkb_geometry);
            DELETE FROM scootdetectors WHERE ogc_fid NOT IN
                (SELECT DISTINCT ON (detector_n) ogc_fid FROM scootdetectors);
            ALTER TABLE scootdetectors
                DROP COLUMN dataset,
                DROP COLUMN docname,
                DROP COLUMN docpath,
                DROP COLUMN loop_type,
                DROP COLUMN objectid,
                DROP COLUMN ogc_fid,
                DROP COLUMN unique_id;
            ALTER TABLE scootdetectors ADD PRIMARY KEY (detector_n);
            """

        elif self.data_directory == "ukmap.gdb":
            sql_code = """
            DROP INDEX IF EXISTS ukmap_gix;
            CREATE INDEX ukmap_gix ON ukmap USING GIST(shape);
            ALTER TABLE ukmap
                DROP COLUMN calcaulated_height_of_building,
                DROP COLUMN geographic_entity_type;
            ALTER TABLE ukmap RENAME COLUMN altertative_style_code TO alternative_style_code;
            ALTER TABLE ukmap RENAME COLUMN catrographic_display_angle TO cartographic_display_angle;
            ALTER TABLE ukmap ADD PRIMARY KEY (objectid);
            """

        if sql_code:
            self.logger.info("Running SQL code:")
            for line in sql_code.split("\n"):
                self.logger.info(green(line.strip()))
            with self.dbcnxn.engine.connect() as conn:
                conn.execute(sql_code)

        self.logger.info("Finished database configuration")

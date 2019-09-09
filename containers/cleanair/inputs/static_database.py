"""
Upload static data currently held in geodatabase/shape file format in Azure
Convert to PostgreSQL using ogr2ogr and upload to the inputs DB
"""
import glob
import os
import subprocess
from sqlalchemy.exc import OperationalError
from ..databases import Connector
from ..loggers import get_logger, green


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

        # Preprocess the UKMap data, keeping only useful columns
        if self.data_directory == "ukmap.gdb":
            extra_args += ["-lco", "FID=geographic_type_number",
                           "-dialect", "OGRSQL",
                           "-sql", "SELECT " + ", ".join([
                               "CAST(geographic_type_number AS integer) AS geographic_type_number",
                               # NB. The next command is a single string split across mulitple lines for readability
                               "CAST(CONCAT('20', SUBSTR(CONCAT('00', date_of_feature_edit), -6, 2), '-',"
                               "SUBSTR(date_of_feature_edit, -4, 2), '-',"
                               "SUBSTR(date_of_feature_edit, -2)) AS date) AS date_of_feature_edit",
                               "feature_type",
                               "landuse",
                               # "CAST(altertative_style_code AS integer) AS alternative_style_code",
                               # "owner_user_name",
                               # "building_name",
                               # "CAST(primary_number AS integer) AS primary_number",
                               # "primary_number_suffix",
                               # "CAST(secondary_number AS integer) AS secondary_number",
                               # "secondary_number_suffix",
                               # "CAST(number_end_of_range AS integer) AS number_end_of_range",
                               # "number_end_of_range_suffix",
                               # "road_name_primary",
                               # "road_name_secondary",
                               # "locality_name",
                               # "area_name",
                               # "county_region_name",
                               # "country",
                               "postcode",
                               #   "address_range_type",
                               #   "CAST(blpu_number AS integer) AS blpu_number",
                               #   "address_type",
                               #   "CAST(cartographic_annotation_point AS integer) AS cartographic_annotation_point",
                               #   "name_of_point_of_interest",
                               #   "description_of_point_of_interest",
                               #   "CAST(retail_classification_code AS integer) AS retail_classification_code",
                               #   "retail_description",
                               #   "above_retail_type",
                               #   "road_number_code",
                               #   "CAST(catrographic_display_angle AS integer) AS cartographic_display_angle",
                               #   "CAST(source_of_height_data AS integer) AS source_of_height_data",
                               "CAST(height_of_base_of_building AS float)",
                               # "CAST(height_of_top_of_building AS float) AS height_of_top_of_building",
                               "CAST(calcaulated_height_of_building AS float) AS calculated_height_of_building",
                               "shape_length",
                               "shape_area",
                               "shape"]) + " FROM BASE_HB0_complete_merged"]
            self.logger.info("Please note that this dataset requires a lot of SQL processing so upload will be slow")

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

        Ensuring there is an index on the geometry column
        Dropping (some) duplicate rows
        Dropping duplicate/unnecessary columns
        Converting some column types
        Adding a primary key
        """
        self.logger.info("Configuring database table: %s", green(self.table_name))
        sql_commands = []

        if self.data_directory == "canyonslondon":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS canyonslondon_wkb_geometry_geom_idx
                   ON canyonslondon USING GIST(wkb_geometry);""",
                """ALTER TABLE canyonslondon
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
                   DROP COLUMN sum_shape_;""",
                """ALTER TABLE canyonslondon
                   ALTER fictitious TYPE bool
                   USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE canyonslondon ADD PRIMARY KEY (toid);""",
            ]

        elif self.data_directory == "glahexgrid":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS glahexgrid_wkb_geometry_geom_idx
                   ON glahexgrid USING GIST(wkb_geometry);""",
                """ALTER TABLE glahexgrid
                       DROP COLUMN col_id,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN row_id;""",
                """ALTER TABLE glahexgrid ADD PRIMARY KEY (hex_id);""",
            ]

        elif self.data_directory == "londonboundary":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS londonboundary_wkb_geometry_geom_idx
                   ON londonboundary USING GIST(wkb_geometry);""",
                """ALTER TABLE londonboundary
                       DROP COLUMN ogc_fid,
                       DROP COLUMN sub_2006,
                       DROP COLUMN sub_2009;""",
                """ALTER TABLE londonboundary
                       ALTER ons_inner TYPE bool
                       USING CASE WHEN ons_inner='F' THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE londonboundary ADD PRIMARY KEY (gss_code);""",
            ]

        elif self.data_directory == "oshighwayroadlink":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS oshighwayroadlink_wkb_geometry_geom_idx
                   ON oshighwayroadlink USING GIST(wkb_geometry);""",
                """ALTER TABLE oshighwayroadlink
                       DROP COLUMN cyclefacil,
                       DROP COLUMN elevatio_1,
                       DROP COLUMN elevationg,
                       DROP COLUMN identifi_1,
                       DROP COLUMN identifier,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN roadstruct,
                       DROP COLUMN roadwidtha,
                       DROP COLUMN roadwidthm;""",
                """ALTER TABLE oshighwayroadlink
                    ALTER fictitious TYPE bool
                    USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE oshighwayroadlink ADD PRIMARY KEY (toid);"""
            ]

        elif self.data_directory == "scootdetectors":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS scootdetectors_wkb_geometry_geom_idx
                   ON scootdetectors USING GIST(wkb_geometry);""",
                """DELETE FROM scootdetectors WHERE ogc_fid NOT IN
                       (SELECT DISTINCT ON (detector_n) ogc_fid FROM scootdetectors);""",
                """ALTER TABLE scootdetectors
                       DROP COLUMN dataset,
                       DROP COLUMN docname,
                       DROP COLUMN docpath,
                       DROP COLUMN loop_id,
                       DROP COLUMN loop_type,
                       DROP COLUMN objectid,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN unique_id;""",
                """ALTER TABLE scootdetectors RENAME COLUMN itn_date TO date_installed;""",
                """ALTER TABLE scootdetectors RENAME COLUMN date_updat TO date_updated;""",
                """ALTER TABLE scootdetectors ADD PRIMARY KEY (detector_n);""",
            ]

        elif self.data_directory == "ukmap.gdb":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS ukmap_shape_geom_idx ON ukmap USING GIST(shape);""",
            ]

        for sql_command in sql_commands:
            self.logger.info("Running SQL command:")
            for line in sql_command.split("\n"):
                self.logger.info(green(line.strip()))
            with self.dbcnxn.engine.connect() as conn:
                try:
                    conn.execute(sql_command)
                except OperationalError:
                    self.logger.warning("Database connection lost while running statement.")
        self.logger.info("Finished database configuration")

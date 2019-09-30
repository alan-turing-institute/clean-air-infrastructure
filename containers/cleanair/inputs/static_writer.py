"""
Upload static data currently held in geodatabase/shape file format in Azure
Convert to PostgreSQL using ogr2ogr and upload to the inputs DB
"""
import glob
import os
import subprocess
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import CreateSchema
from ..databases import DBWriter, InterestPoint
from ..loggers import get_logger, green


class StaticWriter(DBWriter):
    """Manage interactions with the static database on Azure"""
    def __init__(self, **kwargs):
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.data_directory = None
        self.table_name = None

        # Ensure that extensions have been enabled
        self.dbcnxn.ensure_extensions()

        # Ensure that the datasources schema exists
        self.dbcnxn.ensure_schema("datasources")

        # Ensure that interest_points table exists
        if not self.dbcnxn.engine.dialect.has_schema(self.dbcnxn.engine, "buffers"):
            self.dbcnxn.engine.execute(CreateSchema("buffers"))
        InterestPoint.__table__.create(self.dbcnxn.engine, checkfirst=True)

        # Initialise parent classes
        super().__init__(**kwargs)

    def upload_static_files(self):
        """Upload static data to the inputs database"""
        # Look for static files in /data then set the file and table names
        try:
            self.data_directory = os.listdir("/data")[0]
            self.logger.debug("data_directory: %s", self.data_directory)
        except FileNotFoundError:
            raise FileNotFoundError("Could not find any static files in /data. Did you mount this path?")
        self.table_name = self.data_directory.replace(".gdb", "")

        # Check whether table exists - excluding reflected tables
        existing_table_names = self.dbcnxn.engine.table_names(schema="datasources")
        if self.table_name in existing_table_names:
            self.logger.info("Skipping upload for %s as the remote table already exists", green(self.table_name))
            return False

        # Get the connection string
        connection_string = " ".join(["host={host}", "port={port}", "user={username}", "password={password}",
                                      "dbname={db_name}", "sslmode={ssl_mode}"]).format(**self.dbcnxn.connection_info)

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
                               # "address_range_type",
                               # "CAST(blpu_number AS integer) AS blpu_number",
                               # "address_type",
                               # "CAST(cartographic_annotation_point AS integer) AS cartographic_annotation_point",
                               # "name_of_point_of_interest",
                               # "description_of_point_of_interest",
                               # "CAST(retail_classification_code AS integer) AS retail_classification_code",
                               # "retail_description",
                               # "above_retail_type",
                               # "road_number_code",
                               # "CAST(catrographic_display_angle AS integer) AS cartographic_display_angle",
                               # "CAST(source_of_height_data AS integer) AS source_of_height_data",
                               "CAST(height_of_base_of_building AS float)",
                               # "CAST(height_of_top_of_building AS float) AS height_of_top_of_building",
                               "CAST(calcaulated_height_of_building AS float) AS calculated_height_of_building",
                               "shape_length AS geom_length",
                               "shape_area AS geom_area",
                               "shape AS geom"]) + " FROM BASE_HB0_complete_merged"]
            self.logger.info("Please note that this dataset requires a lot of SQL processing so upload will be slow")

        # Force scoot detector geometries to POINT
        elif self.data_directory == "scootdetectors":
            extra_args += ["-nlt", "POINT"]

        # Run ogr2ogr
        self.logger.info("Uploading static data to table %s in %s",
                         green(self.table_name), green(self.dbcnxn.connection_info["db_name"]))
        subprocess.run(["ogr2ogr", "-overwrite", "-progress",
                        "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.data_directory),
                        "--config", "PG_USE_COPY", "YES",
                        "-t_srs", "EPSG:4326",
                        "-lco", "SCHEMA=datasources",
                        "-nln", self.table_name] + extra_args)
        return True

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
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN wkb_geometry TO geom;""",
                """CREATE INDEX IF NOT EXISTS canyonslondon_wkb_geometry_geom_idx
                       ON datasources.canyonslondon USING GIST(geom);""",
                """ALTER TABLE datasources.canyonslondon
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
                       DROP COLUMN provenance,
                       DROP COLUMN shape_le_1,
                       DROP COLUMN sum_length,
                       DROP COLUMN sum_shape_;""",
                """ALTER TABLE datasources.canyonslondon
                       ALTER fictitious TYPE bool
                       USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE datasources.canyonslondon
                       ALTER operationa TYPE bool
                       USING CASE WHEN operationa='Open' THEN TRUE ELSE FALSE END;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN roadclassi TO road_classification;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN routehiera TO route_hierarchy;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN operationa TO operational;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN directiona TO directionality;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN matchstatu TO match_status;""",
                """ALTER TABLE datasources.canyonslondon RENAME COLUMN shape_leng TO geom_length;""",
                """ALTER TABLE datasources.canyonslondon ADD PRIMARY KEY (toid);""",
            ]

        elif self.data_directory == "glahexgrid":
            sql_commands = [
                """ALTER TABLE datasources.glahexgrid RENAME COLUMN wkb_geometry TO geom;""",
                """CREATE INDEX IF NOT EXISTS glahexgrid_wkb_geometry_geom_idx
                       ON datasources.glahexgrid USING GIST(geom);""",
                """ALTER TABLE datasources.glahexgrid
                       DROP COLUMN centroid_x,
                       DROP COLUMN centroid_y,
                       DROP COLUMN ogc_fid;""",
                """ALTER TABLE datasources.glahexgrid ADD COLUMN centroid geometry(POINT, 4326);""",
                """UPDATE datasources.glahexgrid SET centroid = ST_centroid(geom);""",
                """ALTER TABLE datasources.glahexgrid ADD PRIMARY KEY (hex_id);""",
                """INSERT INTO buffers.interest_points(source, location, point_id)
                       SELECT 'hexgrid', centroid, uuid_generate_v4()
                       FROM datasources.glahexgrid;""",
                """ALTER TABLE datasources.glahexgrid ADD COLUMN point_id uuid;""",
                """ALTER TABLE datasources.glahexgrid
                       ADD CONSTRAINT fk_glahexgrid_id FOREIGN KEY (point_id)
                       REFERENCES buffers.interest_points(point_id) ON DELETE CASCADE ON UPDATE CASCADE;""",
                """UPDATE datasources.glahexgrid
                       SET point_id = buffers.interest_points.point_id
                       FROM buffers.interest_points
                       WHERE datasources.glahexgrid.centroid = buffers.interest_points.location;""",
                """ALTER TABLE datasources.glahexgrid DROP COLUMN centroid;""",
            ]

        elif self.data_directory == "londonboundary":
            sql_commands = [
                """ALTER TABLE datasources.londonboundary RENAME COLUMN wkb_geometry TO geom;""",
                """CREATE INDEX IF NOT EXISTS londonboundary_wkb_geometry_geom_idx
                       ON datasources.londonboundary USING GIST(geom);""",
                """ALTER TABLE datasources.londonboundary
                       DROP COLUMN ogc_fid,
                       DROP COLUMN sub_2006,
                       DROP COLUMN sub_2009;""",
                """ALTER TABLE datasources.londonboundary
                       ALTER ons_inner TYPE bool
                       USING CASE WHEN ons_inner='F' THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE datasources.londonboundary ADD PRIMARY KEY (gss_code);""",
            ]

        elif self.data_directory == "oshighwayroadlink":
            sql_commands = [
                """ALTER TABLE datasources.oshighwayroadlink RENAME COLUMN wkb_geometry TO geom;""",
                """CREATE INDEX IF NOT EXISTS oshighwayroadlink_wkb_geometry_geom_idx
                       ON datasources.oshighwayroadlink USING GIST(geom);""",
                """ALTER TABLE datasources.oshighwayroadlink
                       DROP COLUMN cyclefacil,
                       DROP COLUMN elevatio_1,
                       DROP COLUMN elevationg,
                       DROP COLUMN identifi_1,
                       DROP COLUMN identifier,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN roadstruct,
                       DROP COLUMN roadwidtha,
                       DROP COLUMN roadwidthm;""",
                """ALTER TABLE datasources.oshighwayroadlink
                       ALTER fictitious TYPE bool
                       USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""",
                """ALTER TABLE datasources.oshighwayroadlink ADD PRIMARY KEY (toid);"""
            ]

        elif self.data_directory == "scootdetectors":
            sql_commands = [
                # Tidy up scootdetectors table
                """DELETE FROM datasources.scootdetectors WHERE ogc_fid NOT IN
                       (SELECT DISTINCT ON (detector_n) ogc_fid FROM datasources.scootdetectors);""",
                """ALTER TABLE datasources.scootdetectors
                       DROP COLUMN cell,
                       DROP COLUMN dataset,
                       DROP COLUMN docname,
                       DROP COLUMN docpath,
                       DROP COLUMN easting,
                       DROP COLUMN loop_id,
                       DROP COLUMN loop_type,
                       DROP COLUMN northing,
                       DROP COLUMN objectid,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN unique_id;""",
                """ALTER TABLE datasources.scootdetectors RENAME COLUMN itn_date TO date_installed;""",
                """ALTER TABLE datasources.scootdetectors RENAME COLUMN date_updat TO date_updated;""",
                """ALTER TABLE datasources.scootdetectors ADD PRIMARY KEY (detector_n);""",
                # Move geometry data to interest_points table - note that some detectors share a location
                """INSERT INTO buffers.interest_points(source, location, point_id)
                       SELECT DISTINCT on (wkb_geometry) 'scoot', wkb_geometry, uuid_generate_v4()
                       FROM datasources.scootdetectors;""",
                """ALTER TABLE datasources.scootdetectors ADD COLUMN point_id uuid;""",
                """ALTER TABLE datasources.scootdetectors
                       ADD CONSTRAINT fk_scootdetectors_id FOREIGN KEY (point_id)
                       REFERENCES buffers.interest_points(point_id) ON DELETE CASCADE ON UPDATE CASCADE;""",
                """UPDATE datasources.scootdetectors
                       SET point_id = buffers.interest_points.point_id
                       FROM buffers.interest_points
                       WHERE datasources.scootdetectors.wkb_geometry = buffers.interest_points.location;""",
                """ALTER TABLE datasources.scootdetectors DROP COLUMN wkb_geometry;""",
            ]

        elif self.data_directory == "ukmap.gdb":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS ukmap_geom_geom_idx ON datasources.ukmap USING GIST(geom);""",
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
                finally:
                    conn.close()
        self.logger.info("Finished database configuration")

    def update_remote_tables(self):
        """Attempt to upload static files and configure the tables if successful"""
        if self.upload_static_files():
            self.configure_tables()

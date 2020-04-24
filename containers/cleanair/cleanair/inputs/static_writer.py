"""
Upload static data currently held in geodatabase/shape file format in Azure
Convert to PostgreSQL using ogr2ogr and upload to the inputs DB
"""
import glob
import os
import subprocess
from sqlalchemy.exc import OperationalError
from ..databases import DBWriter
from ..databases.tables import MetaPoint
from ..loggers import get_logger, green


class StaticWriter(DBWriter):
    """Manage interactions with the static database on Azure"""

    def __init__(self, target_file, schema, table, **kwargs):
        # Initialise parent classes
        super().__init__(initialise_tables=False, **kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Attributes: directory where local data is held and name of remote table
        self.target_file = target_file
        self.table_name = table
        self.schema = schema

        # Ensure that the necessary schemas exist
        for schema in [self.schema, "interest_points"]:
            self.dbcnxn.ensure_schema(schema)
        self.dbcnxn.ensure_extensions()

        # Ensure that interest_points table exists
        MetaPoint.__table__.create(self.dbcnxn.engine, checkfirst=True)

    # @property
    # def schema(self):
    #     """Get schema that the current dataset will live under"""
    #     return self.schemas[self.table_name]

    @property
    def schema_table(self):
        """Get schema and table where the current dataset will live"""
        return "{}.{}".format(self.schema, self.table_name)

    def upload_static_files(self):
        """Upload static data to the inputs database"""

        # Check whether table exists - excluding reflected tables
        existing_table_names = self.dbcnxn.engine.table_names(schema=self.schema)
        if self.table_name in existing_table_names:
            self.logger.info(
                "Skipping upload for %s as the remote table already exists",
                green(self.table_name),
            )
            return False

        # Get the connection string
        cnxn_string = " ".join(
            [
                "dbname={db_name}",
                "port={port}",
                "user={username}",
                "password={password}",
                "host={host}",
                "sslmode={ssl_mode}",
            ]
        ).format(**self.dbcnxn.connection_info)

        # Add additional arguments if the input data contains shape files
        extra_args = ["-lco", "GEOMETRY_NAME=geom"]

        if glob.glob("/{}/*.shp".format(self.target_file)):
            extra_args += ["-nlt", "PROMOTE_TO_MULTI", "-lco", "precision=NO"]

        # Preprocess the UKMap data, keeping only useful columns
        if self.table_name == "ukmap":
            extra_args += [
                "-lco",
                "FID=geographic_type_number",
                "-dialect",
                "OGRSQL",
                "-dim",
                "XY",
                "-sql",
                "SELECT "
                + ", ".join(
                    [
                        "CAST(geographic_type_number AS integer) AS geographic_type_number",
                        "CAST(CONCAT('20', SUBSTR(CONCAT('00', date_of_feature_edit), -6, 2), '-',"
                        + "SUBSTR(date_of_feature_edit, -4, 2), '-',"
                        + "SUBSTR(date_of_feature_edit, -2)) AS date) AS date_of_feature_edit",
                        "feature_type",
                        "landuse",
                        "postcode",
                        "CAST(height_of_base_of_building AS float)",
                        "CAST(calcaulated_height_of_building AS float) AS calculated_height_of_building",
                        "shape_length AS geom_length",
                        "shape_area AS geom_area",
                        "shape AS geom",
                    ]
                )
                + " FROM BASE_HB0_complete_merged",
            ]
            self.logger.info(
                "Please note that this dataset requires SQL pre-processing so upload will be slow (~1hr)"
            )

        # Force scoot detector geometries to POINT
        elif self.table_name == "scoot_detector":
            extra_args += ["-nlt", "POINT"]

        elif self.table_name == "rectgrid_100":
            extra_args += ["-s_srs", "EPSG:27700"]
        # Run ogr2ogr
        self.logger.info(
            "Uploading static data to table %s in %s",
            green(self.table_name),
            green(self.dbcnxn.connection_info["db_name"]),
        )
        try:
            command = [
                "ogr2ogr",
                "-overwrite",
                "-progress",
                "-f",
                "PostgreSQL",
                "PG:{}".format(cnxn_string),
                "{}".format(self.target_file),
                "--config",
                "PG_USE_COPY",
                "YES",
                "-t_srs",
                "EPSG:4326",
                "-lco",
                "SCHEMA={}".format(self.schema),
                "-nln",
                self.table_name,
            ] + extra_args

            subprocess.run(
                command, check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.error("Running ogr2ogr failed!")
            raise
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

        if self.table_name == "hexgrid":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS hexgrid_geom_geom_idx
                       ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       DROP COLUMN centroid_x,
                       DROP COLUMN centroid_y,
                       DROP COLUMN ogc_fid;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD COLUMN centroid geometry(POINT, 4326);""".format(
                    self.schema_table
                ),
                """UPDATE {} SET centroid = ST_centroid(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD PRIMARY KEY (hex_id);""".format(
                    self.schema_table
                ),
                """INSERT INTO interest_points.meta_point(source, location, id)
                       SELECT 'hexgrid', centroid, uuid_generate_v4()
                       FROM {};""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD COLUMN point_id uuid;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ADD CONSTRAINT fk_hexgrid_id FOREIGN KEY (point_id)
                       REFERENCES interest_points.meta_point(id)
                       ON DELETE CASCADE ON UPDATE CASCADE;""".format(
                    self.schema_table
                ),
                """UPDATE {0}
                       SET point_id = meta_points.id
                       FROM (SELECT * FROM interest_points.meta_point WHERE source = 'hexgrid') as meta_points
                       WHERE {0}.centroid = meta_points.location;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} DROP COLUMN centroid;""".format(self.schema_table),
            ]

        elif self.table_name == "rectgrid_100":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS rectgrid_100_geom_geom_idx
                       ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       DROP COLUMN objectid,
                       DROP COLUMN orig_fid;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD COLUMN centroid geometry(POINT, 4326);""".format(
                    self.schema_table
                ),
                """UPDATE {} SET centroid = ST_centroid(geom);""".format(
                    self.schema_table
                ),
                """CREATE INDEX IF NOT EXISTS rectgrid_100_centroid_geom_idx
                       ON {} USING GIST(centroid);""".format(
                    self.schema_table
                ),
                """INSERT INTO interest_points.meta_point(source, location, id)
                       SELECT 'grid_100', centroid, uuid_generate_v4()
                       FROM {};""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD COLUMN point_id uuid;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ADD CONSTRAINT fk_rectgrid_100_id FOREIGN KEY (point_id)
                       REFERENCES interest_points.meta_point(id)
                       ON DELETE CASCADE ON UPDATE CASCADE;""".format(
                    self.schema_table
                ),
                """UPDATE {0}
                       SET point_id = meta_points.id
                       FROM (SELECT * FROM interest_points.meta_point WHERE source = 'grid_100') as meta_points
                       WHERE {0}.centroid = meta_points.location;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} DROP COLUMN centroid;""".format(self.schema_table),
            ]

        elif self.table_name == "london_boundary":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS london_boundary_geom_geom_idx
                       ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       DROP COLUMN ogc_fid,
                       DROP COLUMN sub_2006,
                       DROP COLUMN sub_2009;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER ons_inner TYPE bool
                       USING CASE WHEN ons_inner='F' THEN FALSE ELSE TRUE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN nonld_area TO non_ld_area;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD PRIMARY KEY (gss_code);""".format(
                    self.schema_table
                ),
            ]

        elif self.table_name == "oshighway_roadlink":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS oshighway_roadlink_geom_geom_idx
                       ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       DROP COLUMN alternat_1,
                       DROP COLUMN alternat_2,
                       DROP COLUMN alternat_3,
                       DROP COLUMN alternat_4,
                       DROP COLUMN alternatei,
                       DROP COLUMN cyclefacil,
                       DROP COLUMN elevatio_1,
                       DROP COLUMN elevationg,
                       DROP COLUMN identifi_1,
                       DROP COLUMN identifier,
                       DROP COLUMN ogc_fid,
                       DROP COLUMN provenance,
                       DROP COLUMN roadclas_1,
                       DROP COLUMN roadname1_,
                       DROP COLUMN roadname11,
                       DROP COLUMN roadname2_,
                       DROP COLUMN roadname21,
                       DROP COLUMN roadstruct,
                       DROP COLUMN roadwidtha,
                       DROP COLUMN roadwidthm;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER fictitious TYPE bool
                       USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER trunkroad TYPE bool
                       USING CASE WHEN trunkroad=0 THEN FALSE ELSE TRUE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER primaryrou TYPE bool
                       USING CASE WHEN primaryrou=0 THEN FALSE ELSE TRUE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN directiona TO directionality;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN formofway TO form_of_way;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN matchstatu TO match_status;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN operationa TO operational;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN primaryrou TO primary_route;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN reasonforc TO reason_for_change;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN roadclassi TO road_classification;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN routehiera TO route_hierarchy;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN shape_leng TO geom_length;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD PRIMARY KEY (toid);""".format(self.schema_table),
            ]

        elif self.table_name == "scoot_detector":
            sql_commands = [
                # Tidy up scoot_detector table
                """DELETE FROM {0} WHERE ogc_fid NOT IN
                       (SELECT DISTINCT ON (detector_n) ogc_fid FROM {0});""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
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
                       DROP COLUMN unique_id;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN itn_date TO date_installed;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN date_updat TO date_updated;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD PRIMARY KEY (detector_n);""".format(
                    self.schema_table
                ),
                # Add the osgb prefix to the toid column
                """UPDATE {0} SET toid = CONCAT('osgb', toid);""".format(
                    self.schema_table
                ),
                # Move geometry data to interest_points table - note that some detectors share a location
                """INSERT INTO interest_points.meta_point(source, location, id)
                       SELECT DISTINCT on (geom) 'scoot', geom, uuid_generate_v4()
                       FROM {};""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD COLUMN point_id uuid;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ADD CONSTRAINT fk_scoot_detector_id FOREIGN KEY (point_id)
                       REFERENCES interest_points.meta_point(id)
                       ON DELETE CASCADE ON UPDATE CASCADE;""".format(
                    self.schema_table
                ),
                """CREATE UNIQUE INDEX scoot_detector_detector_n_key ON {}(detector_n);""".format(
                    self.schema_table
                ),
                """UPDATE {0}
                       SET point_id = meta_points.id
                       FROM (SELECT * FROM interest_points.meta_point WHERE source = 'scoot') as meta_points
                       WHERE {0}.geom = meta_points.location;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} DROP COLUMN geom;""".format(self.schema_table),
            ]

        elif self.table_name == "street_canyon":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS street_canyon_geom_geom_idx
                       ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
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
                       DROP COLUMN sum_shape_;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER fictitious TYPE bool
                       USING CASE WHEN fictitious=0 THEN FALSE ELSE TRUE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {}
                       ALTER operationa TYPE bool
                       USING CASE WHEN operationa='Open' THEN TRUE ELSE FALSE END;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN directiona TO directionality;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN matchstatu TO match_status;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN operationa TO operational;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN roadclassi TO road_classification;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN routehiera TO route_hierarchy;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} RENAME COLUMN shape_leng TO geom_length;""".format(
                    self.schema_table
                ),
                """ALTER TABLE {} ADD PRIMARY KEY (toid);""".format(self.schema_table),
            ]

        elif self.table_name == "ukmap":
            sql_commands = [
                """CREATE INDEX IF NOT EXISTS ukmap_geom_geom_idx ON {} USING GIST(geom);""".format(
                    self.schema_table
                ),
                """UPDATE {} SET geom = ST_Multi(ST_BuildArea(ST_MakeValid(geom)))
                       WHERE ST_GeometryType(geom)!='ST_MultiPolygon'
                       OR NOT ST_IsValid(geom);""".format(
                    self.schema_table
                ),
                """CREATE INDEX IF NOT EXISTS ukmap_landuse_idx ON {}(landuse);""".format(
                    self.schema_table
                ),
                """CREATE INDEX IF NOT EXISTS ukmap_feature_type_idx ON {}(feature_type);""".format(
                    self.schema_table
                ),
                """CREATE INDEX IF NOT EXISTS ukmap_calculated_height_of_building_idx
                       ON {}(calculated_height_of_building);""".format(
                    self.schema_table
                ),
            ]
            self.logger.info(
                "Please note processing the uploaded data on the server will be slow (~30mins)"
            )

        self.logger.info("Running %i SQL commands:", len(sql_commands))
        for idx, sql_command in enumerate(sql_commands):
            self.logger.info(
                green("{}: ".format(idx) + " ".join(sql_command.split()).strip())
            )
            with self.dbcnxn.engine.connect() as cnxn:
                try:
                    cnxn.execute(sql_command)
                except OperationalError:
                    self.logger.warning(
                        "Database connection lost while running statement."
                    )
                finally:
                    cnxn.close()
        self.logger.info("Finished database configuration")

    def update_remote_tables(self):
        """Attempt to upload static files and configure the tables if successful"""
        if self.upload_static_files():
            self.configure_tables()

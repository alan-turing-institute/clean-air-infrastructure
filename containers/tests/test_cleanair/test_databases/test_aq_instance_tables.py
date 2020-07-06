from typing import Any, Dict, Union
import pandas as pd
from sqlalchemy import inspect
from cleanair.databases import DBWriter
from cleanair.instance import AirQualityInstance
from cleanair.databases.tables import (
    AirQualityDataTable,
    AirQualityModelTable,
    AirQualityResultTable,
)
from cleanair.types import DataConfig, ParamsSVGP



def test_insert_laqn_data_table(
    secretfile: str,
<<<<<<< HEAD
    connection: Any,  # TODO what type is this?
=======
    connection: Any,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
    base_data_id: int,
    no_features_data_config: DataConfig,
    base_aq_preprocessing: Dict,
):
    """Test data is inserted into the air quality data config table.

    Args:
        secretfile: The fixture for secretfiles.
        connection: The fixture for DB connection.
        base_data_config: Air quality data settings.
    """
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    records = [
        dict(
            data_id=base_data_id,
<<<<<<< HEAD
            data_config=base_aq_data_config,
=======
            data_config=no_features_data_config,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
            preprocessing=base_aq_preprocessing,
        )
    ]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")


def test_insert_svgp(
<<<<<<< HEAD
    secretfile: str,
    connection: Any,  # TODO what type is this?
    svgp_model_params: ModelParamSVGP,
    svgp_param_id: str,
=======
    secretfile: str, connection: Any, svgp_model_params: ParamsSVGP, svgp_param_id: str,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
):
    """Test data is inserted into the air quality model table.

    Args:
        secretfile: The fixture for secretfiles.
        connection: The fixture for DB connection.
        svgp_model_params: Simple model parameters for an SVGP.
    """
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    model_name = "svgp"
    records = [
        dict(
            model_name=model_name,
            param_id=svgp_param_id,
            model_param=svgp_model_params,
        )
    ]
    conn.commit_records(records, table=AirQualityModelTable, on_conflict="ignore")


def test_insert_instance(
    secretfile: str,
<<<<<<< HEAD
    connection: Any,  # TODO what type is this?
=======
    connection: Any,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
    svgp_instance: AirQualityInstance,
    no_features_data_config: DataConfig,
    base_aq_preprocessing: Dict,
    svgp_model_params: ParamsSVGP,
):
    """Insert instance into database."""
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    # insert model
    model_name = "svgp"
    records = [
        dict(
            model_name=model_name,
            param_id=svgp_instance.param_id,
            model_param=svgp_model_params,
        )
    ]
    conn.commit_records(records, table=AirQualityModelTable, on_conflict="ignore")

    # insert data
    records = [
        dict(
            data_id=svgp_instance.data_id,
<<<<<<< HEAD
            data_config=base_aq_data_config,
=======
            data_config=no_features_data_config,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
            preprocessing=base_aq_preprocessing,
        )
    ]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")

    # insert instance
    svgp_instance.update_remote_tables()


def test_insert_result_table(
<<<<<<< HEAD
    secretfile: str,
    connection: Any,  # TODO what type is this?
    svgp_result: pd.DataFrame,
=======
    secretfile: str, connection: Any, svgp_result: pd.DataFrame,
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
):
    """Insert fake results into the results air quality table."""
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    records = svgp_result.to_dict("records")
    conn.commit_records(records, table=AirQualityResultTable, on_conflict="ignore")

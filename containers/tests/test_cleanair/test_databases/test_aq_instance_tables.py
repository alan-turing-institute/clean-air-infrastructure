"""Tests for air quality instance tables."""

from typing import Any, Dict
import pandas as pd
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
    connection: Any,
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
            data_config=no_features_data_config,
            preprocessing=base_aq_preprocessing,
        )
    ]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")


def test_insert_svgp(
    secretfile: str, connection: Any, svgp_params_dict: ParamsSVGP, svgp_param_id: str,
):
    """Test data is inserted into the air quality model table.

    Args:
        secretfile: The fixture for secretfiles.
        connection: The fixture for DB connection.
        svgp_params_dict: Simple model parameters for an SVGP.
    """
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    model_name = "svgp"
    records = [
        dict(
            model_name=model_name, param_id=svgp_param_id, model_param=svgp_params_dict,
        )
    ]
    conn.commit_records(records, table=AirQualityModelTable, on_conflict="ignore")


def test_insert_instance(
    secretfile: str,
    connection: Any,
    svgp_instance: AirQualityInstance,
    no_features_data_config: DataConfig,
    base_aq_preprocessing: Dict,
    svgp_params_dict: ParamsSVGP,
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
            model_param=svgp_params_dict,
        )
    ]
    conn.commit_records(records, table=AirQualityModelTable, on_conflict="ignore")

    # insert data
    records = [
        dict(
            data_id=svgp_instance.data_id,
            data_config=no_features_data_config,
            preprocessing=base_aq_preprocessing,
        )
    ]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")

    # insert instance
    svgp_instance.update_remote_tables()


def test_insert_result_table(
    secretfile: str, connection: Any, svgp_result: pd.DataFrame,
):
    """Insert fake results into the results air quality table."""
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    records = svgp_result.to_dict("records")
    conn.commit_records(records, table=AirQualityResultTable, on_conflict="ignore")

"""Fixtures for mixins."""

from typing import Any
from pydantic import BaseModel
from cleanair.experiment import AirQualityInstance
from cleanair.types import ModelName


# pylint: disable=redefined-outer-name
def test_update_remote_tables(
    secretfile: str,
    connection: Any,
    simple_config: BaseModel,
    simple_params: BaseModel,
    simple_preprocessing: BaseModel,
) -> None:
    """Test the update mixin write to tables."""
    instance = AirQualityInstance(
        simple_config,
        ModelName.svgp,
        simple_params,
        preprocessing=simple_preprocessing,
        secretfile=secretfile,
        connection=connection,
    )
    instance.update_remote_tables()
    with instance.dbcnxn.open_session() as session:
        instance_row = session.query(instance.instance_table)
        model_row = session.query(instance.model_table)
        data_row = session.query(instance.data_table)
        assert instance_row.count() == 1
        assert model_row.count() == 1
        assert data_row.count() == 1
        loaded_config = simple_config.__class__(**data_row.one().data_config)
        loaded_preprocessing = simple_preprocessing.__class__(
            **data_row.one().preprocessing
        )
        loaded_params = simple_params.__class__(**model_row.one().model_params)

        # check keys and value of loaded data config
        for key, value in loaded_config:
            assert hasattr(simple_config, key)
            assert getattr(simple_config, key) == value

        # check keys and value of loaded preprocessing
        for key, value in loaded_preprocessing:
            assert hasattr(simple_preprocessing, key)
            assert getattr(simple_preprocessing, key) == value

        # check keys and value of loaded model_params
        for key, value in loaded_params:
            assert hasattr(simple_params, key)
            assert getattr(simple_params, key) == value

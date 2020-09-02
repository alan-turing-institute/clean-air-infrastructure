"""Fixtures for mixins."""

from datetime import datetime
from typing import Any, List
import pytest
from pydantic import BaseModel
from cleanair.instance import AirQualityInstance
from cleanair.types import ModelName


class SimpleConfig(BaseModel):
    start: datetime
    upto: datetime
    sensors: List[str]


class SimpleParams(BaseModel):
    maxiter: int
    likelihood: str


class SimplePreprocessing(BaseModel):
    normalise: bool


@pytest.fixture(scope="function")
def simple_config(dataset_start_date, dataset_end_date) -> SimpleConfig:
    return SimpleConfig(start=dataset_start_date, upto=dataset_end_date, sensors=["A"])


@pytest.fixture(scope="function")
def simple_params() -> SimpleParams:
    return SimpleParams(maxiter=10, likelihood="gaussian")


@pytest.fixture(scope="function")
def simple_preprocessing() -> SimplePreprocessing:
    return SimplePreprocessing(normalise=True)


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
        loaded_config = SimpleConfig(**data_row.one().data_config)
        loaded_preprocessing = SimplePreprocessing(**data_row.one().preprocessing)
        loaded_params = SimpleParams(**model_row.one().model_params)

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

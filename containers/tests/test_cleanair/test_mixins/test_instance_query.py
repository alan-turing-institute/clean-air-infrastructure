"""Test instance queries"""

from cleanair.experiment import AirQualityInstance
from cleanair.databases.queries import AirQualityInstanceQuery
from cleanair import types


def test_query_instance(
    secretfile, connection_class, valid_full_config, mrdgp_model_params
):
    """Test an instance can be queried."""
    instance = AirQualityInstance(
        valid_full_config,
        types.ModelName.mrdgp,
        mrdgp_model_params,
        secretfile=secretfile,
        connection=connection_class,
    )
    instance.update_remote_tables()
    query = AirQualityInstanceQuery(secretfile=secretfile, connection=connection_class)
    queried_instance = query.query_instance(instance.instance_id)
    assert queried_instance.data_id == instance.data_id
    assert queried_instance.param_id == instance.param_id
    assert queried_instance.git_hash == instance.git_hash
    assert (
        queried_instance.data_config.train_end_date
        == instance.data_config.train_end_date
    )
    assert queried_instance.model_name == instance.model_name


from typing import Any
from cleanair.databases import DBWriter
from cleanair.instance import Instance
from cleanair.databases.tables import AirQualityDataTable

def test_insert_aq_data_table(
    secretfile: str,
    connection: Any,    # TODO what type is this?
    base_aq_data_config: dict,
    base_aq_preprocessing: dict,
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
    data_id = Instance.hash_dict(dict(base_aq_data_config, **base_aq_preprocessing))
    records = [dict(
        data_id=data_id,
        data_config=base_aq_data_config,
        preprocessing=base_aq_preprocessing,
    )]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")

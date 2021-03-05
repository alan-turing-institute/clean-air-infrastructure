"""Test update experiment"""

from datetime import datetime
from cleanair.databases import DBReader
from cleanair.databases.queries import AirQualityInstanceQuery, AirQualityResultQuery
from cleanair.mixins.availability_mixins import LAQNAvailabilityMixin
from cleanair.types import Source


def num_hours_between_datetime(start: datetime, end: datetime) -> int:
    """Number of hours between two datetimes (rounded down if fractional)"""
    seconds_in_hour = 60 ** 2
    return int((end - start).total_seconds() / seconds_in_hour)


def test_num_hours_between_datetime():
    """Test num hours"""
    start = datetime(2021, 1, 1, 0, 0, 0)
    assert num_hours_between_datetime(start, datetime(2021, 1, 1, 5, 0, 0)) == 5
    assert num_hours_between_datetime(start, datetime(2021, 1, 1, 5, 1, 0)) == 5
    assert num_hours_between_datetime(start, datetime(2021, 1, 2, 0, 0, 0)) == 24
    assert num_hours_between_datetime(start, start) == 0


class LAQNQuery(LAQNAvailabilityMixin, DBReader):
    """LAQN query"""


class TestUpdateAirQualityExperiment:
    """The results are written to the database"""

    def test_setup(self, fake_cleanair_dataset, update_aq_experiment):
        """Add the fake dataset to the DB"""

    def test_update_remote_tables(
        self, secretfile, connection_class, update_aq_experiment
    ):
        """Test the instances are written to the DB"""
        # check instances we added in test_setup
        assert update_aq_experiment.get_num_instances() == 1
        update_aq_experiment.update_remote_tables()
        instance_query = AirQualityInstanceQuery(
            secretfile, connection=connection_class
        )
        instance_df = instance_query.get_instances_with_params(
            instance_ids=update_aq_experiment.get_instance_ids(), output_type="df"
        )
        assert (
            instance_df.instance_id.to_list() == update_aq_experiment.get_instance_ids()
        )

    def test_query_laqn(self, secretfile, connection_class, update_aq_experiment):
        """Check point ids are in database"""
        laqn_query = LAQNQuery(secretfile=secretfile, connection=connection_class)
        laqn_df = laqn_query.get_laqn_open_sites(output_type="df")
        assert len(laqn_df) > 0
        instance_id = update_aq_experiment.get_instance_ids()[0]
        data_config = update_aq_experiment.get_instance(instance_id).data_config
        point_ids = set(laqn_df.point_id.apply(str).to_list())
        assert set(map(str, data_config.train_interest_points[Source.laqn])).issubset(
            point_ids
        )

    def test_update_result_tables(
        self, secretfile, connection_class, update_aq_experiment
    ):
        """Test the results are written to the DB"""
        # write results to DB
        update_aq_experiment.update_remote_tables()
        update_aq_experiment.update_result_tables()

        # setup query of results
        source = Source.laqn
        result_query = AirQualityResultQuery(
            secretfile=secretfile, connection=connection_class
        )
        instance_id = update_aq_experiment.get_instance_ids()[0]
        result_df = result_query.query_results(instance_id, source, output_type="df")
        instance = update_aq_experiment.get_instance(instance_id)
        data_config = instance.data_config

        # calculate size of expected data
        num_training_hours = num_hours_between_datetime(
            data_config.train_start_date, data_config.train_end_date
        )
        num_test_hours = num_hours_between_datetime(
            data_config.pred_start_date, data_config.pred_end_date
        )
        num_training_points = len(data_config.train_interest_points[source])
        num_test_points = len(data_config.pred_interest_points[source])
        expected_num_training_rows = num_training_hours * num_training_points
        expected_num_test_rows = num_test_hours * num_test_points

        pred_training_df = result_df.loc[
            result_df["measurement_start_utc"] < data_config.train_end_date
        ]
        pred_test_df = result_df.loc[
            result_df["measurement_start_utc"] >= data_config.pred_start_date
        ]

        # check result queried from DB has the right number of rows
        assert len(pred_training_df) == expected_num_training_rows
        assert len(pred_test_df) == expected_num_test_rows

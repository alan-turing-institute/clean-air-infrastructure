"""Test update experiment"""

from cleanair.databases.queries import AirQualityInstanceQuery


class TestUpdateAirQualityExperiment:
    """The results are written to the database"""

    def test_setup(self, fake_cleanair_dataset, update_aq_experiment):
        """Add the fake dataset to the DB"""

    def test_update_remote_tables(self, update_aq_experiment, secretfile, connection):
        """Test the instances are written to the DB"""
        # check instances we added in test_setup
        assert update_aq_experiment.get_num_instances() == 1
        update_aq_experiment.update_remote_tables()
        instance_query = AirQualityInstanceQuery(secretfile, connection=connection)
        instance_df = instance_query.get_instances_with_params(
            instance_ids=update_aq_experiment.get_instance_ids(), output_type="df"
        )
        assert (
            instance_df.instance_id.to_list() == update_aq_experiment.get_instance_ids()
        )

    def test_update_result_tables(self, update_aq_experiment):
        """Test the results are written to the DB"""

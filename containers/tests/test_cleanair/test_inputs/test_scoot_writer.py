# init

# get_remote_filenames

# get_existing_scoot_data

# request_remote_data
# combine_by_detector_id
# aggregate_scoot_data
# update_remote_table
import pytest
from dateutil import rrule
from datetime import timedelta


def test_scoot_detector(
    scoot_single_detector_generator, scoot_writer, dataset_start_date, dataset_end_date
):
    "Test that we can verify that a set of scoot detectors have data for a given hour"

    # Insert data for a single scoot detector into the database for the full dataset time period
    # scoot_single_detector_generator.update_remote_tables()
    sensor_ids = scoot_writer.scoot_detectors(
        detectors=["N04/161a1"], output_type="list"
    )

    # Check the detector exists for all hours
    date_range = rrule.rrule(
        rrule.HOURLY,
        dtstart=dataset_start_date,
        until=dataset_end_date - timedelta(hours=1),
    )

    # Check the detector has data for the daterange of interest
    assert all(
        map(
            lambda d: scoot_writer.check_detectors_processed(d, [sensor_ids[0]]),
            date_range,
        )
    )

    # But not for other times
    assert not scoot_writer.check_detectors_processed(
        max(date_range) + timedelta(hours=1), [sensor_ids[0]]
    )

    # And not for any other sensors as we only inserted data for one
    assert not any(
        map(
            lambda d: scoot_writer.check_detectors_processed(d, sensor_ids[1:]),
            date_range,
        )
    )

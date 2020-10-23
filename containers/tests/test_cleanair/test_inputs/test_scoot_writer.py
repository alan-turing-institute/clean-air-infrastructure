import pytest
import pandas as pd
from pandas.util.testing import assert_frame_equal
import numpy as np
from dateutil import rrule
from datetime import timedelta


def test_scoot_detector(
    scoot_single_detector_generator, scoot_writer, dataset_start_date, dataset_end_date
):
    "Test that we can verify that a set of scoot detectors have data for a given hour"

    scoot_single_detector_generator.update_remote_tables()
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


def test_process_hour(scoot_detector_single_hour, scoot_writer, dataset_start_date):
    "Test we can process an hour correctly"

    # # Check request_remote_data is patched (arguments not used)
    remote_data = scoot_writer.request_remote_data(
        dataset_start_date, detector_ids = []
    )
    # assert remote_data.equals(
    #     request_remote_data(dataset_start_date, dataset_start_date, [])
    # )

    # Check the aggregate_scoot_data method now returns its input dataframe after patching
    aggregated_df = (
        scoot_writer.aggregate_scoot_data_hour(remote_data)
        .sort_values(["detector_id", "measurement_start_utc"])
        .astype(
            {
                "measurement_start_utc": np.datetime64,
                "measurement_end_utc": np.datetime64,
            }
        )
    )

    # Ensure same row and column ordering
    expected_aggregated_df = scoot_detector_single_hour[0].sort_values(
        ["detector_id", "measurement_start_utc"]
    )[aggregated_df.columns]

    # Assert aggregated_df is now the input df
    assert_frame_equal(aggregated_df, expected_aggregated_df)

    # Test process hour
    # Process data and insert into database
    scoot_writer.process_hour(dataset_start_date)

    # Read data from database
    retrieved_data = scoot_writer.scoot_readings(
        dataset_start_date, with_location=False, output_type="df"
    )

    cols = ["detector_id", "measurement_start_utc", "n_vehicles_in_interval"]

    # Ensure indices match and drop na rows from database data
    expected_cols_df = expected_aggregated_df[cols].copy()
    retrieved_cols_df = (
        retrieved_data[cols]
        .copy()
        .sort_values(["detector_id", "measurement_start_utc"])
    )

    expected_cols_df.reset_index(drop=True, inplace=True)
    retrieved_cols_df_drop_null = retrieved_cols_df.dropna(
        how="any", subset=["n_vehicles_in_interval"]
    ).reset_index(drop=True)

    # Check data in database is expected
    assert_frame_equal(
        retrieved_cols_df_drop_null, expected_cols_df,
    )

    # Check the missing hour is for the missing detector
    null_entries = retrieved_cols_df[retrieved_cols_df.isnull().any(axis=1)][
        "detector_id"
    ].tolist()

    assert len(null_entries) == 1
    assert null_entries[0] == scoot_detector_single_hour[1]

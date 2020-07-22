"""
Given a model data object, check that the data matches the config.
"""
import pytest

# from cleanair.types import Species, TargetDict
from cleanair.databases import DBWriter


class TestRaw:
    def test_setup(self, secretfile, connection_class):
        """Insert test data"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            # writer.commit_records(
            #     video_stat_records, on_conflict="overwrite", table=JamCamVideoStats,
            # )
        except IntegrityError:
            pytest.fail("Dummy data insert")


# def test_training_dicts(model_data):
#     """Check the shape of all the numpy arrays are correct."""
#     # load the dicts from modeldata
#     training_data_dict = model_data.get_training_data_arrays(dropna=False)
#     x_train = training_data_dict["X"]
#     y_train = training_data_dict["Y"]

#     # checks for satellite
#     assert not model_data.config["include_satellite"] or "satellite" in x_train
#     assert not model_data.config["include_satellite"] or "satellite" in y_train

#     # checks that each pollutant has a key in y_train for each source
#     all_train_sources = (
#         model_data.config["train_sources"]
#         if not model_data.config["include_satellite"]
#         else model_data.config["train_sources"] + ["satellite"]
#     )
#     for source in all_train_sources:
#         # check all training sources exist in the dicts
#         assert source in x_train
#         assert source in y_train

#         # check the shape of x_train
#         if source == "satellite":
#             assert len(x_train[source].shape) == 3
#         else:
#             assert len(x_train[source].shape) == 2

#         # check y_train
#         for pollutant in model_data.config["species"]:
#             assert y_train[source][pollutant].shape[0] == x_train[source].shape[0]
#         validate_target(y_train[source])


# def test_pred_dict(model_data):
#     """
#     Check the test set is in the right format.
#     """
#     predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)
#     x_test = predict_data_dict["X"]
#     y_test = predict_data_dict["Y"]
#     assert "satellite" not in x_test

#     for source in model_data.config["pred_sources"]:
#         # check x test
#         assert source in x_test
#         assert len(x_test[source].shape) == 2
#         assert x_test[source].shape[1] == len(model_data.config["x_names"])

#         # check y test
#         assert source in y_test
#         assert len(model_data.config["species"]) == len(y_test[source])
#         validate_target(y_test[source])


# def validate_target(Y: TargetDict) -> bool:
#     """Check the shapes and structure of Y."""
#     for pollutant, array in Y.items():
#         print(pollutant)
#         assert Species.has_key(pollutant)
#         assert len(array.shape) == 2
#         assert array.shape[1] == 1

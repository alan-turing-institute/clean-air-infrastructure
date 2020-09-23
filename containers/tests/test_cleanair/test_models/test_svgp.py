"""Test the SVGP based on a simple LAQN dataset."""


from cleanair.models import ModelDataExtractor, SVGP


# ToDo: Write tests for models
# class TestSVGP:
#     """Class for testing the SVGP on LAQN data."""

#     def test_setup(self, fake_cleanair_dataset):
#         pass

#     def test_svgp_training(
#         self, svgp_model_params, laqn_training_data, laqn_full_config
#     ) -> None:
#         """Test the SVGP trains."""
#         model_data = ModelDataExtractor()
#         model = SVGP(svgp_model_params)
#         X_train, Y_train, index_train = model_data.get_data_arrays(
#             laqn_full_config, laqn_training_data, prediction=False,
#         )
#         model.fit(X_train, Y_train)

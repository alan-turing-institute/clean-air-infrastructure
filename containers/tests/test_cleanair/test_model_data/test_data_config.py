"""
Tests related to the ModelConfig class
"""
import pytest
from enum import Enum
from dateutil.parser import isoparse
from datetime import timedelta
from pydantic import ValidationError
from cleanair.models import ModelConfig
from cleanair.types.dataset_types import BaseConfig, FullConfig

from cleanair.types import Species, Source, FeatureNames, FeatureBufferSize
from cleanair.databases import DBWriter
from cleanair.databases.tables import MetaPoint
from cleanair.exceptions import MissingFeatureError, MissingSourceError


class TestModelConfig:
    def test_setup(self, fake_cleanair_dataset):
        """Insert test data"""

        pass

    def test_generate_config(self, model_config):

        try:
            model_config.generate_data_config(
                "2020-01-01",
                48,
                48,
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Source.hexgrid],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                Source.laqn,
                "svgp",
            )
        except ValueError as e:
            pytest.fail(e)

    @pytest.mark.parametrize(
        "trainupto,train_sources,pred_sources,species,features,buffer_sizes,norm_by,model_type",
        [
            # Uses an invalid source
            pytest.param(
                "2020-01-01",
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Source.hexgrid],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                "not_a_source",
                "svgp",
            ),
            # Species rather than source in pred source
            pytest.param(
                "2020-01-01",
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Species.NO2],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                Source.laqn,
                "svgp",
            ),
        ],
    )
    def test_generate_config_invalid(
        self,
        model_config,
        trainupto,
        train_sources,
        pred_sources,
        species,
        features,
        buffer_sizes,
        norm_by,
        model_type,
    ):
        "Test parameter validation"

        with pytest.raises(ValidationError):
            model_config.generate_data_config(
                trainupto,
                48,
                48,
                train_sources,
                pred_sources,
                species,
                features,
                buffer_sizes,
                norm_by,
                model_type,
            )

    def test_validation_static_features(
        self, valid_config, model_config, static_feature_records
    ):
        """Check static features raise error when missing"""

        # All static features in database
        assert {i.feature_name for i in static_feature_records} == set(
            model_config.get_available_static_features(output_type="list")
        )

        # Check feature availability doesn't raise an error
        try:
            model_config.check_features_available(
                valid_config.features,
                valid_config.train_start_date,
                valid_config.pred_end_date,
            )
        except Exception:
            pytest.fail("Unexpected error")

        class FakeFeature(str, Enum):

            fake_feature = "fake_feature"

        # Check error raised when features missing
        with pytest.raises(MissingFeatureError):
            model_config.check_features_available(
                [FakeFeature.fake_feature],
                valid_config.train_start_date,
                valid_config.pred_end_date,
            )

    def test_validation_source_available(
        self, valid_config, model_config, static_feature_records
    ):

        # All sources in database
        assert {i.feature_source.value for i in static_feature_records}.issubset(
            set(model_config.get_available_sources(output_type="list"))
        )

        # Check source availability doesn't raise an error
        try:
            model_config.check_sources_available(valid_config.train_sources)
        except Exception:
            pytest.fail("Unexpected error")
        try:
            model_config.check_sources_available(valid_config.pred_sources)
        except Exception:
            pytest.fail("Unexpected error")

        class FakeSource(str, Enum):
            fake_source = "fake_source"

        # Check error raised when features missing
        with pytest.raises(MissingSourceError):
            model_config.check_sources_available([FakeSource.fake_source])

    def test_validate_config(self, valid_config, model_config):
        "Check all validations pass"

        try:
            model_config.validate_config(valid_config)
        except Exception:
            pytest.raises("Unexpected error")

    @pytest.mark.parametrize(
        "interest_points_name", [("train_interest_points"), ("pred_interest_points")],
    )
    def test_get_interest_point_ids(
        self, valid_config, model_config, interest_points_name
    ):
        "Check we get all interest points"

        interest_points = getattr(valid_config, interest_points_name)
        sources = interest_points.keys()

        all_interest_points = model_config.get_interest_point_ids(interest_points)

        for source in sources:

            with model_config.dbcnxn.open_session() as session:

                meta_ids = (
                    session.query(MetaPoint.id).filter(MetaPoint.source == source).all()
                )

            meta_ids = [str(i.id) for i in meta_ids]
            interest_ids = all_interest_points[source]

            assert set(meta_ids) == set(interest_ids)

    def test_generate_full_config(self, valid_config, model_config):

        try:
            full_config = model_config.generate_full_config(valid_config)

        except ValidationError:
            pytest.raises("Full config failed")

"""
Fixtures for the cleanair module.
"""
# pylint: disable=redefined-outer-name,C0103
from typing import Tuple
from datetime import datetime, timedelta
import pytest
from dateutil import rrule
from dateutil.parser import isoparse
import numpy as np
import numpy.typing as npt
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    MetaPoint,
    LAQNSite,
    LAQNReading,
    AQESite,
    AQEReading,
    SatelliteBox,
    SatelliteGrid,
    StaticFeature,
    SatelliteForecast,
)
from cleanair.databases.tables.fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AQESiteSchema,
    AQEReadingSchema,
    StaticFeaturesSchema,
    SatelliteBoxSchema,
    SatelliteGridSchema,
    SatelliteForecastSchema,
)
from cleanair.experiment import AirQualityInstance
from cleanair.dataset import ModelConfig, ModelData
from cleanair.types import (
    BaseModelParams,
    DataConfig,
    FeatureBufferSize,
    StaticFeatureNames,
    KernelParams,
    KernelType,
    ModelName,
    MRDGPParams,
    Source,
    Species,
    SVGPParams,
)
from cleanair.data_generators.scoot_generator import ScootGenerator


# pylint: disable=W0613
@pytest.fixture(scope="class")
def valid_config(dataset_start_date, dataset_end_date, num_forecast_days):
    "Valid config for 'fake_cleanair_dataset' fixture"

    return DataConfig(
        **{
            "train_start_date": dataset_start_date,
            "train_end_date": dataset_end_date,
            "pred_start_date": dataset_end_date,
            "pred_end_date": dataset_end_date + timedelta(days=num_forecast_days),
            "include_prediction_y": False,
            "train_sources": ["laqn", "aqe", "satellite"],
            "pred_sources": ["laqn", "aqe", "satellite", "hexgrid"],
            "train_interest_points": {"laqn": "all", "aqe": "all", "satellite": "all"},
            "pred_interest_points": {
                "laqn": "all",
                "aqe": "all",
                "satellite": "all",
                "hexgrid": "all",
            },
            "species": ["NO2"],
            "static_features": [
                "total_road_length",
                "total_a_road_length",
                "total_a_road_primary_length",
                "total_b_road_length",
                "grass",
                "building_height",
                "water",
                "park",
                "max_canyon_narrowest",
                "max_canyon_ratio",
            ],
            "dynamic_features": [],
            "buffer_sizes": ["1000", "500"],
            "norm_by": "laqn",
        }
    )


@pytest.fixture(scope="class")
def valid_full_config(valid_config, model_config, fake_cleanair_dataset):
    "Generate a full configuration file"
    return model_config.generate_full_config(valid_config)


@pytest.fixture(scope="module")
def dataset_start_date():
    "Fake dataset start date"
    return isoparse("2020-01-01")


@pytest.fixture(scope="module")
def dataset_end_date():
    "Fake dataset end date"
    return isoparse("2020-01-05")


@pytest.fixture(scope="function")
def fit_start_time() -> datetime:
    """Datetime for when model started fitting."""
    return datetime(2020, 1, 5, 1, 0, 0)


@pytest.fixture(scope="module")
def num_forecast_days():
    "Number of days for the model to forecast on."
    return 2


@pytest.fixture(scope="module")
def site_open_date(dataset_start_date):
    "Fake date for air quality sensors to open on"
    return dataset_start_date - timedelta(days=365)


@pytest.fixture(scope="module")
def site_closed_date(dataset_start_date):
    "Site close date before the measurement period"
    return dataset_start_date - timedelta(days=100)


@pytest.fixture(scope="module")
def meta_within_london():
    """Meta points within London for laqn and aqe"""

    return [
        MetaPointSchema(source=source)
        for i in range(10)
        for source in [Source.laqn, Source.aqe]
    ]


@pytest.fixture(scope="module")
def meta_within_london_closed():
    """Meta points within London for laqn and aqe"""

    return [
        MetaPointSchema(source=source)
        for i in range(10)
        for source in [Source.laqn, Source.aqe]
    ]


@pytest.fixture(scope="module")
def meta_outside_london():
    """Meta points outside london for laqn and aqe"""

    locations = [
        [-2.658500, 51.834700],
        [2.59890, 48.41120],
        [-1.593061, 53.936595],
        [-1.999790, 53.172000],
    ]

    return [
        MetaPointSchema(
            source=source, location=f"SRID=4326;POINT({point[0]} {point[1]})"
        )
        for point in locations
        for source in [Source.laqn, Source.aqe]
    ]


@pytest.fixture(scope="module")
def aqe_sites_open(meta_within_london, meta_outside_london, site_open_date):
    "Create AQE sites which are open"
    meta_recs = meta_within_london + meta_outside_london

    return [
        AQESiteSchema(point_id=rec.id, date_opened=site_open_date)
        for rec in meta_recs
        if rec.source == Source.aqe
    ]


@pytest.fixture(scope="module")
def aqe_sites_closed(meta_within_london_closed, site_open_date, site_closed_date):
    "Create Aqe sites which are closed"
    return [
        AQESiteSchema(
            point_id=rec.id, date_opened=site_open_date, date_closed=site_closed_date
        )
        for rec in meta_within_london_closed
        if rec.source == Source.aqe
    ]


@pytest.fixture(scope="module")
def aqe_site_records(aqe_sites_open, aqe_sites_closed):
    "Create data for AQESite with a few closed sites"

    return aqe_sites_open + aqe_sites_closed


@pytest.fixture(scope="module")
def laqn_sites_open(meta_within_london, meta_outside_london, site_open_date):
    "Create LAQN sites which are open"
    meta_recs = meta_within_london + meta_outside_london

    return [
        LAQNSiteSchema(point_id=rec.id, date_opened=site_open_date)
        for rec in meta_recs
        if rec.source == Source.laqn
    ]


@pytest.fixture(scope="module")
def laqn_sites_closed(meta_within_london_closed, site_open_date, site_closed_date):
    "Create LAQN sites which are closed"
    return [
        LAQNSiteSchema(
            point_id=rec.id, date_opened=site_open_date, date_closed=site_closed_date
        )
        for rec in meta_within_london_closed
        if rec.source == Source.laqn
    ]


@pytest.fixture(scope="module")
def laqn_site_records(laqn_sites_open, laqn_sites_closed):
    "Create data for AQESite with a few closed sites"

    return laqn_sites_open + laqn_sites_closed


@pytest.fixture(scope="module")
def laqn_reading_records(laqn_site_records, dataset_start_date, dataset_end_date):
    """LAQN reading records assuming full record set with all species at every sensor and no missing data"""

    laqn_readings = []
    for site in laqn_site_records:

        if not site.date_closed:

            for species in Species:

                for measurement_start_time in rrule.rrule(
                    rrule.HOURLY,
                    dtstart=dataset_start_date,
                    until=dataset_end_date,
                ):

                    laqn_readings.append(
                        LAQNReadingSchema(
                            site_code=site.site_code,
                            species_code=species,
                            measurement_start_utc=measurement_start_time,
                        )
                    )

    return laqn_readings


@pytest.fixture(scope="module")
def aqe_reading_records(aqe_site_records, dataset_start_date, dataset_end_date):
    """AQE reading records assuming full record set with all species at every sensor and no missing data"""
    aqe_readings = []
    for site in aqe_site_records:

        if not site.date_closed:

            for species in Species:

                for measurement_start_time in rrule.rrule(
                    rrule.HOURLY,
                    dtstart=dataset_start_date,
                    until=dataset_end_date,
                ):

                    aqe_readings.append(
                        AQEReadingSchema(
                            site_code=site.site_code,
                            species_code=species,
                            measurement_start_utc=measurement_start_time,
                        )
                    )

    return aqe_readings


@pytest.fixture(scope="module")
def satellite_box_records():
    "Locations (centres) of satellite tiles"
    # Set of grid center locations over london
    locations = [
        (-0.45, 51.65),
        (-0.35, 51.65),
        (-0.25, 51.65),
        (-0.15, 51.65),
        (-0.05, 51.65),
        (0.05, 51.65),
        (0.15, 51.65),
        (0.25, 51.65),
        (-0.45, 51.55),
        (-0.35, 51.55),
        (-0.25, 51.55),
        (-0.15, 51.55),
        (-0.05, 51.55),
        (0.05, 51.55),
        (0.15, 51.55),
        (0.25, 51.55),
        (-0.45, 51.45),
        (-0.35, 51.45),
        (-0.25, 51.45),
        (-0.15, 51.45),
        (-0.05, 51.45),
        (0.05, 51.45),
        (0.15, 51.45),
        (0.25, 51.45),
        (-0.45, 51.35),
        (-0.35, 51.35),
        (-0.25, 51.35),
        (-0.15, 51.35),
        (-0.05, 51.35),
        (0.05, 51.35),
        (0.15, 51.35),
        (0.25, 51.35),
    ]

    return [SatelliteBoxSchema(centroid=loc) for loc in locations]


@pytest.fixture(scope="module")
def satellite_meta_point_and_box_records(satellite_box_records):
    "Get satellite meta points and satellite interest point to box map"

    def build_satellite_grid(
        point: Tuple[float, float],
        half_grid: float,
        n_points_lat: int,
        n_points_lon: int,
    ) -> npt.NDArray:
        "Return a grid of satellite points centred at a grid square"
        lat_space = np.linspace(
            point[0] - half_grid + (half_grid / n_points_lat),
            point[0] + half_grid - (half_grid / n_points_lat),
            n_points_lat,
        )
        lon_space = np.linspace(
            point[1] - half_grid + (half_grid / n_points_lon),
            point[1] + half_grid - (half_grid / n_points_lon),
            n_points_lon,
        )
        # Convert the linear-spaces into a grid
        return np.array([[lat, lon] for lon in lon_space for lat in lat_space])

    all_sat_metapoints = []
    all_sat_box_map = []
    for sat_box in satellite_box_records:

        sat_grid = build_satellite_grid(sat_box.centroid_tuple, 0.05, 12, 8)

        for entry in sat_grid:

            meta_point = MetaPointSchema(
                source=Source.satellite,
                location=f"SRID=4326;POINT({entry[0]} {entry[1]})",
            )

            sat_map = SatelliteGridSchema(point_id=meta_point.id, box_id=sat_box.id)

            all_sat_metapoints.append(meta_point)
            all_sat_box_map.append(sat_map)

    return all_sat_metapoints, all_sat_box_map


@pytest.fixture(scope="module")
def satellite_forecast(
    satellite_box_records,
    dataset_start_date,
    dataset_end_date,
):
    """Generate satellitee forecast data"""

    box_ids = [i.id for i in satellite_box_records]
    all_satellite_forecast = []
    for box in box_ids:
        for species in Species:
            for reference_start_utc in rrule.rrule(
                rrule.DAILY,
                dtstart=dataset_start_date,
                until=dataset_end_date,
            ):
                for measurement_start_utc in rrule.rrule(
                    rrule.HOURLY,
                    dtstart=reference_start_utc,
                    count=72,
                ):

                    all_satellite_forecast.append(
                        SatelliteForecastSchema(
                            reference_start_utc=reference_start_utc,
                            measurement_start_utc=measurement_start_utc,
                            species_code=species.value,
                            box_id=box,
                        )
                    )

    return all_satellite_forecast


@pytest.fixture(scope="module")
def meta_records(
    meta_within_london,
    meta_within_london_closed,
    meta_outside_london,
    satellite_meta_point_and_box_records,
):
    "Concatenate all meta records"

    return (
        meta_within_london
        + meta_within_london_closed
        + meta_outside_london
        + satellite_meta_point_and_box_records[0]
    )


@pytest.fixture(scope="module")
def static_feature_records(meta_records):
    """Static features records"""
    static_features = []
    for rec in meta_records:
        for feature in StaticFeatureNames:

            static_features.append(
                StaticFeaturesSchema(
                    point_id=rec.id, feature_name=feature, feature_source=rec.source
                )
            )

    return static_features


@pytest.fixture(scope="class")
def fake_laqn_static_dataset(
    secretfile,
    connection_class,
    meta_records,
    laqn_site_records,
    laqn_reading_records,
    static_feature_records,
):
    """Only insert laqn and static features."""

    writer = DBWriter(secretfile=secretfile, connection=connection_class)

    # Insert meta data
    writer.commit_records(
        [i.dict() for i in meta_records],
        on_conflict="overwrite",
        table=MetaPoint,
    )

    # Insert LAQNSite data
    writer.commit_records(
        [i.dict() for i in laqn_site_records],
        on_conflict="overwrite",
        table=LAQNSite,
    )

    # Insert LAQNReading data
    writer.commit_records(
        [i.dict() for i in laqn_reading_records],
        on_conflict="overwrite",
        table=LAQNReading,
    )

    # Insert static features data
    writer.commit_records(
        [i.dict() for i in static_feature_records],
        on_conflict="overwrite",
        table=StaticFeature,
    )


# pylint: disable=R0913
@pytest.fixture(scope="class")
def fake_cleanair_dataset(
    secretfile,
    connection_class,
    fake_laqn_static_dataset,
    aqe_site_records,
    aqe_reading_records,
    satellite_box_records,
    satellite_meta_point_and_box_records,
    satellite_forecast,
):
    """Insert a fake air quality dataset into the database"""

    writer = DBWriter(secretfile=secretfile, connection=connection_class)

    # Insert AQESite data
    writer.commit_records(
        [i.dict() for i in aqe_site_records],
        on_conflict="overwrite",
        table=AQESite,
    )

    # Insert AQEReading data
    writer.commit_records(
        [i.dict() for i in aqe_reading_records],
        on_conflict="overwrite",
        table=AQEReading,
    )

    # Insert satellite box records
    writer.commit_records(
        [i.dict() for i in satellite_box_records],
        on_conflict="overwrite",
        table=SatelliteBox,
    )

    # Insert satellite box map
    sat_box_map = satellite_meta_point_and_box_records[1]
    # For some reason this insert fails using core
    writer.commit_records(
        [SatelliteGrid(**i.dict()) for i in sat_box_map],
        on_conflict="overwrite",
    )

    # Insert satellite readings
    writer.commit_records(
        [i.dict() for i in satellite_forecast],
        on_conflict="overwrite",
        table=SatelliteForecast,
    )


@pytest.fixture(scope="class")
def laqn_config(dataset_start_date, dataset_end_date, num_forecast_days):
    """LAQN dataset with just one feature."""
    return DataConfig(
        train_start_date=dataset_start_date,
        train_end_date=dataset_end_date,
        pred_start_date=dataset_end_date,
        pred_end_date=dataset_end_date + timedelta(days=num_forecast_days),
        include_prediction_y=False,
        train_sources=[Source.laqn],
        pred_sources=[Source.laqn],
        train_interest_points={Source.laqn.value: "all"},
        pred_interest_points={Source.laqn.value: "all"},
        species=[Species.NO2],
        static_features=[StaticFeatureNames.total_a_road_length],
        dynamic_features=[],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        norm_by=Source.laqn,
        model_type=ModelName.svgp,
    )


@pytest.fixture(scope="class")
def laqn_full_config(fake_laqn_static_dataset, laqn_config, model_config):
    """Generate full config for laqn."""
    model_config.validate_config(laqn_config)
    return model_config.generate_full_config(laqn_config)


@pytest.fixture(scope="function")
def scoot_generator(
    secretfile,
    connection,
    dataset_start_date,
    dataset_end_date,
) -> ScootGenerator:
    """Write scoot data to database"""
    return ScootGenerator(
        start=dataset_start_date.isoformat(),
        upto=dataset_end_date.isoformat(),
        offset=0,
        limit=100,
        secretfile=secretfile,
        connection=connection,
    )


@pytest.fixture(scope="class")
def matern32_params() -> KernelParams:
    """Matern 32 kernel params."""
    return KernelParams(
        name="matern32",
        type=KernelType.matern32,
        lengthscales=1.0,
        variance=1.0,
        ARD=True,
        input_dim=3,
    )


@pytest.fixture(scope="class")
def base_model(matern32_params: KernelParams) -> BaseModelParams:
    """Model params for SVGP and sub-MRDGP"""
    return BaseModelParams(
        kernel=matern32_params,
        likelihood_variance=1.0,
        num_inducing_points=10,
        maxiter=10,
        minibatch_size=10,
    )


@pytest.fixture(scope="class")
def svgp_model_params(base_model: BaseModelParams) -> SVGPParams:
    """Create a model params pydantic class."""
    return SVGPParams(
        **base_model.dict(),
        jitter=0.1,
    )


@pytest.fixture(scope="class")
def mr_linear_params() -> KernelParams:
    """Matern 32 kernel params."""
    return KernelParams(
        name="mr_linear",
        type=KernelType.mr_linear,
        lengthscales=[1.0, 1.0, 1.0],
        variance=[1.0, 1.0, 1.0],
        ARD=True,
        active_dims=[0, 1, 2],
        input_dim=3,
    )


@pytest.fixture(scope="class")
def sub_model(mr_linear_params: KernelParams) -> BaseModelParams:
    """Model params for sub-MRDGP"""
    return BaseModelParams(
        kernel=mr_linear_params,
        likelihood_variance=1.0,
        num_inducing_points=10,
        maxiter=10,
        minibatch_size=10,
    )


@pytest.fixture(scope="class")
def mrdgp_model_params(sub_model: BaseModelParams) -> MRDGPParams:
    """Create MRDGP model params."""
    return MRDGPParams(
        base_laqn=sub_model.copy(),
        base_sat=sub_model.copy(),
        dgp_sat=sub_model.copy(),
        mixing_weight=dict(name="dgp_only", param=None),
        num_prediction_samples=10,
        num_samples_between_layers=10,
    )


@pytest.fixture(scope="class")
def model_config(secretfile, connection_class):
    "Return a ModelConfig instance"
    return ModelConfig(secretfile=secretfile, connection=connection_class)


@pytest.fixture(scope="function")
def model_data(secretfile, connection_class):
    "Return a ModelData instance"
    return ModelData(secretfile=secretfile, connection=connection_class)


@pytest.fixture(scope="function")
def sat_config(dataset_start_date):
    """Satellite dataset with no feature."""
    return DataConfig(
        train_start_date=dataset_start_date,
        train_end_date=dataset_start_date + timedelta(days=1),
        pred_start_date=dataset_start_date + timedelta(days=1),
        pred_end_date=dataset_start_date + timedelta(days=2),
        include_prediction_y=False,
        train_sources=[Source.laqn, Source.satellite],
        pred_sources=[Source.laqn],
        train_interest_points={Source.laqn.value: "all", Source.satellite.value: "all"},
        pred_interest_points={Source.laqn.value: "all", Source.satellite.value: "all"},
        species=[Species.NO2],
        static_features=[StaticFeatureNames.total_a_road_length],
        dynamic_features=[],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        norm_by=Source.laqn,
        model_type=ModelName.mrdgp,
    )


@pytest.fixture(scope="function")
def sat_full_config(sat_config, model_config):
    """Generate full config for laqn + sat."""
    model_config.validate_config(sat_config)
    return model_config.generate_full_config(sat_config)


@pytest.fixture(scope="class")
def laqn_svgp_instance(
    secretfile, connection_class, laqn_full_config, svgp_model_params
):
    """LAQN data and a SVGP model params inside an instance"""
    return AirQualityInstance(
        data_config=laqn_full_config,
        model_name=ModelName.svgp,
        model_params=svgp_model_params,
        secretfile=secretfile,
        connection=connection_class,
    )


@pytest.fixture(scope="function")
def sat_mrdgp_instance(
    secretfile, connection_class, mrdgp_model_params, sat_full_config
):
    """Satellite + LAQN data with MRDGP model params"""
    return AirQualityInstance(
        data_config=sat_full_config,
        model_name=ModelName.mrdgp,
        model_params=mrdgp_model_params,
        secretfile=secretfile,
        connection=connection_class,
    )

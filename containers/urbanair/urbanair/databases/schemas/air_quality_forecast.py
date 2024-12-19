"""Return schemas for air quality forecast routes"""

from typing import List, Dict, Optional, Union
import json
from pydantic import BaseModel
from geojson import Feature
import shapely.wkt
from shapely.geometry import Polygon, MultiPolygon
from urbanair.types import JSONType
from .jamcam import UTCTime


class BaseGeoJson(BaseModel):
    """Tile geometries as GeoJSON feature collection"""

    # Schema attributes
    type: str = "FeatureCollection"
    features: List[Feature]

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        raise NotImplementedError("Must be implemented by child classes")

    class Config:
        """Pydantic configuration"""

        schema_extra: JSONType = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "hex_id": "11481250",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [
                                        [0.23087, 51.603159],
                                        [0.232405, 51.604703],
                                        [0.23532, 51.604648],
                                        [0.236701, 51.603048],
                                        [0.235166, 51.601503],
                                        [0.23225, 51.601559],
                                        [0.23087, 51.603159],
                                    ]
                                ]
                            ],
                        },
                    }
                ],
            }
        }


class ForecastResultGeoJson(BaseGeoJson):
    """Forecast results as GeoJSON feature collection"""

    run_datetime: str

    @staticmethod
    def build_run_datetime(run_datetime: str) -> str:
        "Add run_datetime to GeoJSON endpoint - ! not true geojson"
        return run_datetime

    @staticmethod
    def build_instance_id(instance_id: str) -> str:
        """Add instance_id to the GeoJSON endpoint - ! not true geojson"""
        return instance_id

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        return [
            Feature(
                geometry=try_get_polygon(row["geom"]),  # convert to polygon
                hex_id=row["hex_id"],
                properties={
                    "NO2_mean": row["NO2_mean"],
                    "NO2_var": row["NO2_var"],
                    "measurement_start_utc": json.loads(
                        UTCTime(
                            measurement_start_utc=row["measurement_start_utc"]
                        ).json()
                    )["measurement_start_utc"],
                },
            )
            for row in rows
        ]

    class Config(BaseGeoJson.Config):
        """Pydantic configuration"""

        schema_extra = BaseGeoJson.Config.schema_extra
        for feature in schema_extra["example"]["features"]:  # type: ignore
            feature["properties"] = {
                "NO2_mean": 23.8287315367193,
                "NO2_var": 4.11457257231074,
                "measurement_start_utc": "2020-08-20T15:08:32.555Z",
            }


class ForecastResultJson(UTCTime):
    """Forecast results as JSON"""

    # Schema attributes
    hex_id: str
    NO2_mean: Optional[float]
    NO2_var: Optional[float]

    class Config:
        """Pydantic configuration"""

        orm_mode = True


class ForecastDatasetJson(BaseModel):
    """A set of forecast results with forecast metadata"""

    run_datetime: str
    data: List[ForecastResultJson]

    class Config:
        """Pydantic configuration"""

        orm_mode = True


def try_get_polygon(polygon: Union[Polygon, MultiPolygon]) -> Polygon:
    """Return the first polygon from a multi-polygon

    Args:
        polygon: Can be a polygon or a multi-polygon

    Returns:
        The first polygon in the multi-polygon, or returns the argument
    """
    shape = shapely.wkt.loads(polygon)
    try:
        return list(shape)[0]
    except TypeError:
        return shape


class GeometryGeoJson(BaseGeoJson):
    """Tile geometries as GeoJSON feature collection"""

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        return [
            Feature(
                geometry=try_get_polygon(row["geom"]),  # convert to polygon
                hex_id=row["hex_id"],
            )
            for row in rows
        ]

"""Return schemas for air quality forecast routes"""
from typing import List, Dict
from pydantic import BaseModel
from geojson import Feature
import shapely.wkt
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
                        "id": "00015c34-2c2d-4a55-889f-a458ee780b90",
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

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        return [
            Feature(
                geometry=list(shapely.wkt.loads(row["geom"]))[0],  # convert to polygon
                id=row["point_id"],
                properties={
                    "NO2_mean": row["NO2_mean"],
                    "NO2_var": row["NO2_var"],
                    "measurement_start_utc": row["measurement_start_utc"],
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
    point_id: str
    NO2_mean: float
    NO2_var: float

    class Config:
        """Pydantic configuration"""

        orm_mode = True


class GeometryGeoJson(BaseGeoJson):
    """Tile geometries as GeoJSON feature collection"""

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        return [
            Feature(
                geometry=list(shapely.wkt.loads(row["geom"]))[0],  # convert to polygon
                id=row["point_id"],
            )
            for row in rows
        ]

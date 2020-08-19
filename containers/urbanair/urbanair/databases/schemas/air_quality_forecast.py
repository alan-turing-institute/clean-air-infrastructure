"""Return schemas for air quality forecast routes"""
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel
from geojson import Feature
import shapely.wkt


class ForecastResultGeoJson(BaseModel):
    """Forecast results as GeoJSON feature collection"""

    # Schema attributes
    type: str = "FeatureCollection"
    features: List[Feature]

    @staticmethod
    def build_features(rows: List[Dict]) -> List[Feature]:
        """Construct GeoJSON Features from a list of dictionaries"""
        return [
            Feature(
                geometry=shapely.wkt.loads(row["geom"]),
                id=row["point_id"],
                properties={"NO2_mean": row["NO2_mean"], "NO2_var": row["NO2_var"]},
            )
            for row in rows
        ]

    class Config:
        """Pydantic configuration"""

        schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "00015c34-2c2d-4a55-889f-a458ee780b90",
                        "geometry": {
                            "type": "MultiPolygon",
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
                        "properties": {
                            "NO2_mean": 23.8287315367193,
                            "NO2_var": 4.11457257231074,
                        },
                    }
                ],
            }
        }


class ForecastResultJson(BaseModel):
    """Forecast results as JSON"""

    # Schema attributes
    point_id: str
    measurement_start_utc: datetime
    NO2_mean: float
    NO2_var: float

    class Config:
        """Pydantic configuration"""

        orm_mode = True


class GeometryJson(BaseModel):
    """Forecast results as JSON"""

    # Schema attributes
    point_id: str
    geom: str

    class Config:
        """Pydantic configuration"""

        orm_mode = True

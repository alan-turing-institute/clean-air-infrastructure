"""Return schemas for air quality forecast routes"""
from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, Dict
from geojson import FeatureCollection, Feature
import shapely.wkt


class ForecastResultGeoJson(FeatureCollection):
    """Forecast results as GeoJSON feature collection"""

    def __init__(self, rows: List[Dict]) -> None:
        features = [
            Feature(
                geometry=shapely.wkt.loads(row["location"]),
                id=row["point_id"],
                properties={
                    "NO2_mean": row["NO2_mean"],
                    "NO2_var": row["NO2_var"],
                })
            for row in rows
        ]
        super().__init__(features=features)


class ForecastResultJson(BaseModel):
    """Forecast results as JSON"""
    point_id: str
    measurement_start_utc: datetime
    NO2_mean: float
    NO2_var: float

    class Config:
        orm_mode = True

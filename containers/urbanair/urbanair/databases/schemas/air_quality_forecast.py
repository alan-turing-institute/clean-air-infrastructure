"""Return schemas for air quality forecast routes"""
from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, Dict


class GeoJsonPointCoordinates(BaseModel):
    """GeoJSON point coordinates"""
    latitude: float
    longitude: float


class GeoJsonPointProperties(BaseModel):
    """GeoJSON properties field"""
    NO2_mean: float
    NO2_var: float


class GeoJsonPointGeometry(BaseModel):
    """GeoJSON point feature geometry"""
    type: str = "Point"
    coordinates: GeoJsonPointCoordinates

    @validator("coordinates")
    def convert_string(cls, coordinates: GeoJsonPointCoordinates) -> List[float]:
        """
        Convert GeoJsonPointCoordinates into list.
        Conversion done by @validator, type validation done by GeoJsonPointCoordinates.
        """
        lat, lng = coordinates.dict().values()
        return [lng, lat]


class GeoJsonPointFeature(BaseModel):
    """GeoJSON point feature"""
    type: str = "Feature"
    id: str
    geometry: GeoJsonPointGeometry
    properties: GeoJsonPointProperties

    def __init__(self, row: Dict) -> None:
        super().__init__(
            id=row["point_id"],
            geometry=GeoJsonPointGeometry(coordinates={"latitude": row["latitude"], "longitude": row["longitude"]}),
            properties=GeoJsonPointProperties(NO2_mean=row["NO2_mean"], NO2_var=row["NO2_var"])
        )


class ForecastResultGeoJson(BaseModel):
    """Forecast results as GeoJSON feature collection"""
    type: str = "FeatureCollection"
    features: List[GeoJsonPointFeature]

    def __init__(self, rows: List[Dict]) -> None:
        super().__init__(features=[GeoJsonPointFeature(row) for row in rows])

    class Config:
        arbitrary_types_allowed = True

class ForecastResultJson(BaseModel):
    """Forecast results as JSON"""
    point_id: str
    measurement_start_utc: datetime
    NO2_mean: float
    NO2_var: float

    class Config:
        orm_mode = True

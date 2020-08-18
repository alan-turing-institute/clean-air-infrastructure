"""GeoJSON response for FastAPI"""
from fastapi.responses import JSONResponse


class GeoJSONResponse(JSONResponse):
    """GeoJSON response for FastAPI"""
    media_type = "application/geo+json"

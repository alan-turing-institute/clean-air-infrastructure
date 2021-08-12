"""CSV response for FastAPI"""
from fastapi.responses import PlainTextResponse


class CSVResponse(PlainTextResponse):
    """CSV response for FastAPI"""

    media_type = "text/csv"

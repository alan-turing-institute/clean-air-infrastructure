from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, HTTPException

router = APIRouter()

@router.get(
    "/forecast_info",
    description="GeoJSON: Forecast point data."
)
async def forecast_info(
instance_id: str = Query ('instance_id', description='This is a historic forecast route')
) -> Dict:
    
    return {
        'data': 'A sample route'
    }
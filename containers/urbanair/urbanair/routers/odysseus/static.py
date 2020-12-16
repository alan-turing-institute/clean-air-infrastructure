"""Static routes"""
# pylint: disable=C0116
import os

from fastapi import APIRouter, Request, Response, Depends
from fastapi.templating import Jinja2Templates

from ...security import logged_in

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"
    )
)


@router.get("/usage", include_in_schema=False)
async def usage(request: Request, _=Depends(logged_in)) -> Response:
    return templates.TemplateResponse("usage.html", {"request": request})


@router.get("/map", include_in_schema=False)
async def jamcam_map(request: Request, _=Depends(logged_in)) -> Response:
    return templates.TemplateResponse("map.html", {"request": request})

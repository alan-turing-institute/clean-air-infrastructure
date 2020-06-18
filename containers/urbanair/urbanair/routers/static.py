"""Static routes"""
# pylint: disable=C0116
import os
from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "templates"
    )
)


@router.get("/", include_in_schema=False)
async def home(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/map", include_in_schema=False)
async def map(request: Request) -> Response:
    return templates.TemplateResponse("map.html", {"request": request})


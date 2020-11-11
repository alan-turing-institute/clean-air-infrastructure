"""Static routes"""
# pylint: disable=C0116
import os
from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse


router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"
    )
)


@router.get("/usage", include_in_schema=False)
async def usage(request: Request) -> Response:
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url=request.url_for("home"))
    return templates.TemplateResponse("usage.html", {"request": request})


@router.get("/map", include_in_schema=False)
async def jamcam_map(request: Request) -> Response:
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url=request.url_for("home"))

    return templates.TemplateResponse("map.html", {"request": request})

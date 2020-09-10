"""Static routes"""
# pylint: disable=C0116
from fastapi import APIRouter
from fastapi.responses import RedirectResponse


router = APIRouter()


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="welcome")

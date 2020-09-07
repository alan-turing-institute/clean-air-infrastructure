"""Static routes"""
# pylint: disable=C0116
import os
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse


router = APIRouter()


@router.get("/", include_in_schema=False)
async def home(request: Request) -> RedirectResponse:
    return RedirectResponse(url="welcome")

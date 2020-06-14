from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os


router = APIRouter()
templates = Jinja2Templates(directory=os.path.join("urbanair_fast", "templates"))


@router.get("/map")
async def read_item(request: Request):
    print(os.getcwd())
    return templates.TemplateResponse("map.html", {"request": request},)

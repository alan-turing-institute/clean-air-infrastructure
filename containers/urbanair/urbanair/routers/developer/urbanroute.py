"""Urbanroute API routes"""
# pylint: disable=C0116
from typing import Dict
from fastapi import APIRouter, Depends, Query, Response, HTTPException

router = APIRouter()


@router.get("/welcome", description="An example route")
def welcome() -> Dict:
    return {"Welcome": "add dev routes here"}

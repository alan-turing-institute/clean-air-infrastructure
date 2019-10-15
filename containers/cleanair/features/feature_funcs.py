"""
Functions for feature extractions
"""
from sqlalchemy import func

def sum_area(x):
    """Function to calculate the total area of a geometry"""
    return func.coalesce(func.sum(func.ST_Area(func.Geography(x))), 0.0)

def sum_length(x):
    """Function to calculate the total length of linestring geometries"""
    return func.coalesce(func.sum(func.ST_Length(func.Geography(x))), 0)
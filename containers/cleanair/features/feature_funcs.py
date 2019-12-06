"""
Functions for feature extractions
"""
from sqlalchemy import func


def sum_area(geom):
    """Function to calculate the total area of a geometry"""
    return func.coalesce(func.sum(func.ST_Area(func.Geography(geom))), 0.0)

def sum_length(geom):
    """Function to calculate the total length of linestring geometries"""
    return func.coalesce(func.sum(func.ST_Length(func.Geography(geom))), 0)

def min_(x):
    return func.min(x)

def max_(x):
    return func.max(x)

def avg_(x):
    return func.avg(x)
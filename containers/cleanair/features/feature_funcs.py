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


def sum_(x):
    """sum of x"""
    return func.sum(x)


def min_(x):
    """min of x"""
    return func.min(x)


def max_(x):
    """max of x"""
    return func.max(x)


def avg_(x):
    """avg of x"""
    return func.avg(x)

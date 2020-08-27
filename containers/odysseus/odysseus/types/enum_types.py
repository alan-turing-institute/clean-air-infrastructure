"""Enum types."""

from enum import Enum
import gpflow

class Borough(str, Enum):
    """Enum type for boroughs."""

    kingston_upon_thames = "Kingston upon Thames"
    croydon = "Croydon"
    bromley = "Bromley"
    hounslow = "Hounslow"
    ealing = "Ealing"
    havering = "Havering"
    hillingdon = "Hillingdon"
    harrow = "Harrow"
    brent = "Brent"
    barnet = "Barnet"
    lambeth = "Lambeth"
    southwark = "Southwark"
    lewisham = "Lewisham"
    greenwich = "Greenwich"
    bexley = "Bexley"
    enfield = "Enfield"
    waltham_forest = "Waltham Forest"
    redbridge = "Redbridge"
    sutton = "Sutton"
    richmond_upon_thames = "Richmond upon Thames"
    merton = "Merton"
    wandsworth = "Wandsworth"
    hammersmith_and_fulham = "Hammersmith and Fulham"
    kensington_and_chelsea = "Kensington and Chelsea"
    westminster = "Westminster"
    camden = "Camden"
    tower_hamlets = "Tower Hamlets"
    islington = "Islington"
    hackney = "Hackney"
    haringey = "Haringey"
    newham = "Newham"
    barking_and_bagenham = "Barking and Dagenham"
    city_of_london = "City of London"

class ScootModelName(Enum):

    gpr: gpflow.models.GPR
    svgp: gpflow.models.SVGP

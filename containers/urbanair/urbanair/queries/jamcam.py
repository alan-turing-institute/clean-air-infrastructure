"""
Gets data from sources other than the database
"""
import requests
from ..config import get_settings


def get_tomtom_data(zoom: int, x: int, y: int) -> bytes:
    """
    Relays requests for traffic data to the tomtom api
    :param zoom: int
    :param x: int
    :param y: int
    :return: png image
    """
    key = get_settings().tomtom_api_key
    return requests.get(
        f"https://api.tomtom.com/traffic/map/4/tile/flow/absolute/{zoom}/{x}/{y}.png?key={key}&tileSize=512"
    ).content

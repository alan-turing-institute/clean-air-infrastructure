import asyncio

import pytest

from ..jamcam import csv_from_json_query

async def generate_dictionary(number=0):
    locations = ['London', 'Cambridge, UK', 'Bristol']
    longitudes = [0.002, 0.143, -0.246]
    latitudes = [56.231, -23.411, 0.00]
    output = [{"location": loc, "longitude": lon, "latitude": lat} for loc, lon, lat in zip(locations, longitudes, latitudes)]
    if number:
        output *= number
    await asyncio.sleep(0)
    return output

@pytest.mark.asyncio
async def test_csv_from_json_query():
    result = await csv_from_json_query(function=generate_dictionary)
    assert result.body == b'location,longitude,latitude\nlocation,longitude,latitude\nlocation,longitude,latitude\nlocation,longitude,latitude\n'
    assert result.headers.items() == [('content-length', '112'), ('content-type', 'text/csv; charset=utf-8')]

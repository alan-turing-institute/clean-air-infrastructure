import asyncio
import csv
import datetime
import io
import json

import pytest

from ..jamcam import csv_from_json_query

async def generate_dictionary(number=0, with_commas=False):
    locations = ['London', 'Cambridge', 'Bristol']
    if with_commas:
        locations[1] = locations[1] + ', UK'
    longitudes = [0.002, 0.143, -0.246]
    latitudes = [56.231, -23.411, 0.00]
    dates = [datetime.datetime(2018,1, 2, 23, 2, 12) + datetime.timedelta(days=n)
             for n, loc in enumerate(locations)]
    output = [{"location": loc, "longitude": lon, "latitude": lat, "date": dt}
              for loc, lon, lat, dt in zip(locations, longitudes, latitudes, dates)]
    if number:
        output *= number
    await asyncio.sleep(0)
    return output

def json_format_wanted(value):
    """
    Helper function to define format of dates when serialising dictionaries to
    json
    """
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    return str(value)

def keys_to_number(dictionary):
    """
    Helper function to convert strings into int or float to compare
    dictionaries through a csv reader (all to string) as how json serialises
    (keeping numbers).
    """
    out_dictionary = {}
    func = {True: float, False: int}
    for key, value in dictionary.items():
        out_value = value
        if isinstance(value, str):
            try:
                out_value = func['.' in value](value)
            except ValueError:
                pass
        out_dictionary[key] = out_value
    return out_dictionary

@pytest.mark.asyncio
async def test_csv_from_json_query():
    result = await csv_from_json_query(function=generate_dictionary, with_commas=True)
    fields = ["location,longitude,latitude,date",
              "London,0.002,56.231,2018-01-02T23:02:12",
              "Cambridge, UK,0.143,-23.411,2018-01-03T23:02:12",
              "Bristol,-0.246,0.0,2018-01-04T23:02:12",
              ""]
    expected = "\n".join(fields)
    assert result.body.decode() == expected
    assert result.headers.items() == [('content-length', f'{len(expected)}'),
                                      ('content-type', 'text/csv; charset=utf-8')]


@pytest.mark.asyncio
@pytest.mark.parametrize("commas", [(False), (True)])
async def test_csv_validity(commas):
    json_expected_output = json.dumps(await generate_dictionary(with_commas=commas), default=json_format_wanted)

    result = await csv_from_json_query(function=generate_dictionary, with_commas=commas)
    resultreader = csv.DictReader(io.StringIO(result.body.decode()), delimiter=',')
    result = list(map(keys_to_number, resultreader))
    output = json.dumps(result)

    # Check there are not fields without a header
    assert all([None not in entry.keys() for entry in result])
    assert json_expected_output == output # same input/output



import requests
import os


def AMS_API(token, pollutant, start_date, data_type, name='file.grib2', model='ENSEMBLE',
            level='SURFACE'):

    # token : API token from AMS
    # pollutant: 'NO2', 'NO', 'PM10' etc
    # start_date: as datetime object - reference date for forecast
    # day - day of forecast forward from start_date 0, 1, 2 or 3
    # model - which model to use = ENSEMBLE is median of all others
    # level - either 'SURFACE' or 'ALLLEVELS'

    url = 'https://download.regional.atmosphere.copernicus.eu/services/CAMS50'

    if data_type=='archive':
        _type = 'ANALYSIS'
        time = '-24H-1H'
    elif data_type=='forecast':
        _type = 'FORECAST_'
        time = '0H24H'
    else:
        time = str(day * 24 + 1) + 'H' + str((day + 1) * 24) + 'H'

    referencetime = str(start_date).split(' ')[0] + 'T00:00:00Z'
    package = _type + '_' + pollutant + '_' + level

    params = {'token': token,
              'grid': '0.1',
              'model': model,
              'package': package,
              'time': time,
              'referencetime': referencetime,
              'format': 'GRIB2'
              }

    response = requests.get(url, params=params)

    with open(name, 'wb') as f:
        f.write(response.content)


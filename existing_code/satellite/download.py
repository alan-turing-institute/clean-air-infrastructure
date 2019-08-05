import numpy as np
import pandas as pd
from ams_api import AMS_API  
import pygrib

token = '__T31bRCqssYTUir82rINqlw3YHqa4CnWwEHX60H6Yz6Y__'


downloaded = []
#def AMS_API(token, pollutant, start_date, day, model='ENSEMBLE', level='SURFACE'):
species= 'NO2'
days = [str(i).zfill(2) for i in range(1, 31)]
for day in days:
    if int(day) in downloaded: continue
    date= '2019-02-{day}'.format(day=day)

    print('Downloading date {i}'.format(i=date))
    

    data_type = 'forecast'
    data_type = 'archive'

    AMS_API(token, species, date, data_type, name='data/{species}_{date}_{time}.grib2'.format(species=species,date=date, time=data_type))
#AMS_API(token, 'NO2', '2019 01 02', 0)






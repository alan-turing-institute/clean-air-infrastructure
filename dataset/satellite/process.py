import numpy as np
import pandas as pd
from ams_api import AMS_API  
import pygrib

import matplotlib
matplotlib.use("Qt5agg")
import matplotlib.pyplot as plt


def get_grib_data(filename):
    grb = pygrib.open(filename)

    if grb.messages is 0: return None

    lat, lon = grb[1].latlons()

    total_d = []
    _id = 0

    for g in grb:
        value, lat, lon = g.data(lat1=51.411,lat2=51.616,lon1=-0.203,lon2=0.014)
        date = g.dataDate
        time = g.dataTime
        #value, lat, lon = g.data()

        f= lambda x : np.expand_dims(x.flatten(), -1)
        r= lambda x : np.expand_dims(np.repeat(x, np.prod(value.shape)), -1)

        d = np.concatenate([r(date), r(_id), f(lon), f(lat), f(value)], axis=1)

        print(d)
        print(date)
        print(lon)
        print(lat)
        exit()
        total_d.append(d)
        _id += 1
        if _id is 24: break #one message per hour

    total_d = np.concatenate(total_d, axis=0)
    return total_d

species= 'NO2'
days = [str(i).zfill(2) for i in range(2, 31)]
total_d = []

data_type='archive'

processed = [str(i).zfill(2) for i in range(2, 2)]
for day in days:
    if day in processed: continue
    date= '2019-02-{day}'.format(day=day)
    print(date)

    data = get_grib_data('data/{species}_{date}_{data_type}.grib2'.format(species=species,date=date, data_type=data_type))
    if data is None: continue

    df = pd.DataFrame(data, columns=['date', 'hour',  'lon', 'lat', species.lower()])
    df.to_csv("data_csv/{species}_{date}_{data_type}.csv".format(species=species,date=date, data_type=data_type), index=False)


if False:
    total_d = np.concatenate(total_d, axis=0)
    df = pd.DataFrame(total_d, columns=['date', 'hour',  'lon', 'lat', species.lower()])
    print('saving')
    df.to_csv("all_data_{data_type}.csv".format(data_type=data_type), index=False)

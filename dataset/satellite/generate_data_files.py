import matplotlib
matplotlib.use("Qt5agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd



satellite_df = pd.read_csv('data.csv')

#satellite data is in kg/m3,need to convert to ug/m3 by multiplying by 1000000000

satellite_df['datetime'] = pd.to_datetime(satellite_df['date'].astype(np.int).astype(str) + satellite_df['hour'].astype(int).astype(str), format='%Y%m%d%H')

satellite_df['epoch'] = satellite_df['datetime'].astype('int64')//1e9
satellite_df['x'] = satellite_df['lon']
satellite_df['y'] = satellite_df['lat']


satellite_x = np.array(satellite_df[['lon', 'lat']])
satellite_df['no2'] = np.array(satellite_df[['no2']]*1000000000)
satellite_no2 = satellite_df['no2']


satellite_df.to_csv('satellite_data.csv', header=True, index=False)
satellite_no2.to_csv('satellite_y.csv', header=True, index=False)






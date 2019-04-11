import numpy as np
import pandas as pd

species= 'NO2'
days = [str(i).zfill(2) for i in range(2, 31)]
total_d = []

data_type='archive'

for day in days:
    date= '2019-02-{day}'.format(day=day)

    try:
        df = pd.read_csv("data_csv/{species}_{date}_{data_type}.csv".format(species=species,date=date, data_type=data_type))
        total_d.append(df)
    except:
        continue

total_d = np.concatenate(total_d, axis=0)
df = pd.DataFrame(total_d, columns=['date', 'hour',  'lon', 'lat', species.lower()])
print('saving')
df.to_csv("all_data_{data_type}.csv".format(data_type=data_type), index=False)

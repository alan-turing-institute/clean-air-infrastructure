import json
import pandas as pd

with open('sites.json') as f:
    obj = json.load(f)

arr = []
for site in obj['Sites']['Site']:
    name = site['-SiteName']
    code = site['-SiteCode']
    site_type = site['-SiteType']
    lat = site['-Latitude']
    lon = site['-Longitude']
    date_opened = site['-DateOpened']

    row = [code,name, site_type, date_opened, lat, lon]
    arr.append(row)

df = pd.DataFrame(data=arr, columns=['SiteCode', 'SiteName', 'SiteType','DateOpened', 'Lat', 'Lon'])
df.to_csv('sites.csv', index=False)

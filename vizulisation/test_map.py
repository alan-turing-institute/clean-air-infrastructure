
from folium import plugins
import folium
from owslib.wms import WebMapService


# url = 'http://localhost:8080/geoserver/ows?/'
url = 'http://localhost:8080/geoserver/gwc/service/wms/'

web_map_services = WebMapService(url)

print('\n'.join(web_map_services.contents.keys()))


layer = 'london:latest_forecast'
wms = web_map_services.contents[layer]

# name = wms.title
# print(name)
name = 'latest_forecast'
# lon = (wms.boundingBox[0] + wms.boundingBox[2]) / 2.
# lat = (wms.boundingBox[1] + wms.boundingBox[3]) / 2.
# center = lat, lon

# time_interval = '{0}/{1}'.format(
#     wms.timepositions[0].strip(),
#     wms.timepositions[-1].strip()
# )

# print(time_interval)
time_interval = '2020-01-10T00:00:00.000Z/2020-01-10T05:00:00.000Z'
style = 'london:forecast'

# if style not in wms.styles:
#     style = None


lon, lat = -0.12665390000006, 51.5297753

m = folium.Map(
    location=[lat, lon],
    tiles='Stamen Toner',
    zoom_start=12,
    control_scale=True
)

w = folium.raster_layers.WmsTileLayer(
    url=url,
    name=name,
    fmt='image/png',
    transparent=True,
    layers=layer,
    overlay=True,
    COLORSCALERANGE='1.2,28',
)

w.add_to(m)

time = plugins.TimestampedWmsTileLayers(
    w,
    period='PT1H',
    time_interval=time_interval,
    loop=True,
    auto_play=True,
    transition_time=1000
)

time.add_to(m)

folium.LayerControl().add_to(m)

m.save('images/forecast_time.html')

import folium
from folium import plugins
from folium import WmsTileLayer


m = folium.Map(location=[51.5297753, -0.12665390000006],
               tiles='Stamen Toner',
               zoom_start=12)


folium.Marker([51.5297753, -0.12665390000006], popup='<i>Alan Turing Institute</i>').add_to(m)

# url = 'http://localhost:8080/geoserver/ows?/'
url = 'http://localhost:8080/geoserver/gwc/service/wms/'


wmslay = folium.raster_layers.WmsTileLayer(url,
                                           'london:latest_forecast',
                                           styles='',
                                           fmt='image/png',
                                           transparent=True,
                                           version='1.1.1',
                                           attr='',
                                           name=None,
                                           overlay=True,
                                           control=True,
                                           show=True)
wmslay.add_to(m)

plugins.TimestampedWmsTileLayers([wmslay], loop=True, auto_play=True, period='P1H').add_to(m)


m.save('images/forecast_time.html')

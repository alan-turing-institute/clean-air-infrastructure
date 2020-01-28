from folium.plugins import TimestampedWmsTileLayers
from folium import WmsTileLayer
import folium


m = folium.Map(location=[51.5297753, -0.12665390000006],
               tiles='Stamen Toner',
               zoom_start=12)

# m = folium.Map(location=[51.5297753, -0.12665390000006],
#                zoom_start=12)

folium.Marker([51.5297753, -0.12665390000006], popup='<i>Alan Turing Institute</i>').add_to(m)

# url = 'http://localhost:8080/geoserver/ows?/'
url = 'http://localhost:8080/geoserver/gwc/service/wms/'


# folium.raster_layers.WmsTileLayer(url,
#                                   'london:parks',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:sensor_locs',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:oshighway_roadlink',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:water',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#   show = True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:building_height',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:water_features',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

# folium.raster_layers.WmsTileLayer(url,
#                                   'london:laqn_park_features',
#                                   styles='',
#                                   fmt='image/png',
#                                   transparent=True,
#                                   version='1.1.1',
#                                   attr='',
#                                   name=None,
#                                   overlay=True,
#                                   control=True,
#                                   show=True).add_to(m)

folium.raster_layers.WmsTileLayer(url,
                                  'london:latest_forecast',
                                  styles='',
                                  fmt='image/png',
                                  transparent=True,
                                  version='1.1.1',
                                  attr='',
                                  name=None,
                                  overlay=True,
                                  control=True,
                                  show=True).add_to(m)


m.save('images/forecast.html')

# w0 = WmsTileLayer(
#     'http://this.wms.server/ncWMS/wms',
#     name='Test WMS Data',
#     styles='',
#     fmt='image/png',
#     transparent=True,
#     layers='test_data',
#     COLORSCALERANGE='0,10',
# )
# w0.add_to(m)
# w1 = WmsTileLayer(
#     'http://this.wms.server/ncWMS/wms',
#     name='Test WMS Data',
#     styles='',
#     fmt='image/png',
#     transparent=True,
#     layers='test_data_2',
#     COLORSCALERANGE='0,5',
# )
# w1.add_to(m)
# # Add WmsTileLayers to time control.
# time = TimestampedWmsTileLayers([w0, w1])
# time.add_to(m)
# m.save('index.html')

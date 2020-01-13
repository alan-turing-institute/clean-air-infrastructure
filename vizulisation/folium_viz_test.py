
import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers')
import folium
from folium import WmsTileLayer
from folium.plugins import TimestampedWmsTileLayers
import pandas as pd
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from sqlalchemy import literal, func
import logging
import geopandas as gpd
from cleanair.loggers import get_logger
from cleanair.databases import DBReader, DBWriter
from cleanair.databases.tables import ScootRoadReading, OSHighway



logging.basicConfig()

m = folium.Map(location=[51.5297753, -0.12665390000006],
               tiles='Stamen Toner',
               zoom_start=13)

folium.Marker([51.5297753, -0.12665390000006], popup='<i>Alan Turing Institute</i>').add_to(m)

url = 'http://localhost:8080/geoserver/ows?/'
folium.raster_layers.WmsTileLayer(url,
                                  'london:oshighway_roadlink',
                                  styles='',
                                  fmt='image/png',
                                  transparent=True,
                                  version='1.1.1',
                                  attr='',
                                  name=None,
                                  overlay=True,
                                  control=True,
                                  show=True).add_to(m)

m.save('index.html')

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
m.save('index.html')

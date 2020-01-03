import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers')
import folium
import pandas as pd
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from sqlalchemy import literal, func
from cleanair.databases.tables import ScootRoadReading, OSHighway
from cleanair.databases import DBReader, DBWriter
from cleanair.loggers import get_logger
import logging
import geopandas as gpd

logging.basicConfig()

class ModelDataReader(DBReader, DBWriter):
    """Read data from multiple database tables in order to get data for model fitting"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

    def get_scoot_data(self):

        with self.dbcnxn.open_session() as session:

            scoot_data = session.query(ScootRoadReading) \
                                .filter(ScootRoadReading.measurement_start_utc == '2019-12-10T00:00:00')

            return pd.read_sql(scoot_data.statement, scoot_data.session.bind)

    def get_osh_geoms(self):

        with self.dbcnxn.open_session() as session:

            scoot_data = session.query(OSHighway.toid.label("road_toid"), OSHighway.geom)

            return gpd.read_postgis(scoot_data.statement, scoot_data.session.bind, geom_col='geom')


geo_data = ModelDataReader(secretfile='terraform/.secrets/db_secrets.json')

# scoot_data = geo_data.get_scoot_data()
geom_data = geo_data.get_osh_geoms()
geom_data_json = geom_data.to_json()
   
   
m = folium.Map(location=[ 51.5297753, -0.12665390000006],
                            tiles='Stamen Toner',
                        zoom_start=13)
        
folium.Marker([ 51.5297753, -0.12665390000006], popup='<i>Alan Turing Institute</i>').add_to(m)

# folium.GeoJson(
#     geom_data_json,
#     name='geom'
# ).add_to(m)
# folium.Choropleth(geo_data=geom_data_json, data=scoot_data,
#                 columns=['road_toid', 'flow_raw_count'],
#                 key_on='feature.id',
#                 fill_color='YlGnBu', fill_opacity=0.7, line_opacity=0.2).add_to(m)

m.save('index.html')
import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/docker/')

from datasources import LondonBoundary, LAQNDatabase, HexGrid, UKMap
from datasources.databases import  laqn_tables, Connector
from geoalchemy2 import Geography, Geometry
from geoalchemy2.types import WKBElement
from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_Buffer
from sqlalchemy import func,  and_, cast
import matplotlib.pyplot as plt
import pandas as pd 
import geopandas
import numpy as np 

if __name__ == '__main__':
    

    # Import datasources
    laqn = LAQNDatabase(secretfile = '.db_inputs_local_secret.json')
    hex_grid = HexGrid(secretfile = '.db_inputs_local_secret.json')

    # Import features 
    ukmap = UKMap(secretfile = '.db_inputs_local_secret.json')

    # # Import boundary
    london_boundary = LondonBoundary(secretfile = '.db_inputs_local_secret.json')
    

    london_boundary_df = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement, london_boundary.engine, geom_col='wkb_geometry')
    

    # Process interest points
    # buffer_size = 0.01
    buffer_size = 1000
    laqn_buffers = laqn.query_interest_point_buffers([buffer_size], 
                                                     london_boundary.convex_hull, 
                                                     include_sites=None,
                                                     num_seg_quarter_circle = 8)

    # laqn_buffers_df = pd.read_sql(laqn_buffers.statement, 
    #                                                       laqn.dbcnxn.engine)

   

    laqn.logger.info("Starting execution")
    laqn_buffers_df = geopandas.GeoDataFrame.from_postgis(laqn_buffers.statement, 
                                                          laqn.dbcnxn.engine, 
                                                          geom_col='buffer_' + str(buffer_size))
    laqn.logger.info("Finish execution")

    # # # s = laqn_buffers.subquery()
    # # # with laqn.dbcnxn.open_session() as session:
    # # #     q = session.query(s.c['buffer_' + str(buffer_size)].cast(Geography).ST_Area().label('geom'))

    # # print(np.pi * buffer_size**2, q.first())
    # # # Plots
    # ax_buffers = london_boundary_df.plot(color = 'r', alpha = 0.2) 
    # laqn_buffers_df.plot(ax = ax_buffers, color = 'b')
    

    # # # Process features (Really slow)
    ukmap_features = ukmap.query_features(laqn_buffers, 'buffer_' + str(buffer_size))
    # print(ukmap_features.statement)


    laqn.logger.info("Starting executions")
    ukmap_features_df = pd.read_sql(ukmap_features.statement, ukmap.engine)
    laqn.logger.info("Finish execution")
    print(ukmap_features_df)
    # plt.show()

    
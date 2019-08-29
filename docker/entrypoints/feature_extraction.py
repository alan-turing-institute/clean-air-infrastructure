import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/docker/')

from datasources import LondonBoundary, LAQNDatabase, HexGrid, UKMap
from datasources.databases import  laqn_tables, Connector
from geoalchemy2.types import WKBElement
from geoalchemy2.shape import to_shape
from sqlalchemy import func,  and_
import matplotlib.pyplot as plt
import pandas as pd 
import geopandas

if __name__ == '__main__':
    

    # Import datasources
    laqn = LAQNDatabase(secretfile = '.db_inputs_local_secret.json')
    hex_grid = HexGrid(secretfile = '.db_inputs_local_secret.json')

    # Import features 
    ukmap = UKMap(secretfile = '.db_inputs_local_secret.json')

    # Import boundary
    london_boundary = LondonBoundary(secretfile = '.db_inputs_local_secret.json')
    london_boundary_df = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement, conn.engine, geom_col='wkb_geometry')
    

    # Process interest points
    buffer_size = 0.01
    laqn_buffers = laqn.query_interest_point_buffers([buffer_size], 
                                                     london_boundary.convex_hull, 
                                                     include_sites=None)

    laqn_buffers_df = geopandas.GeoDataFrame.from_postgis(laqn_buffers.statement, 
                                                          laqn.dbcnxn.engine, 
                                                          geom_col='buffer_' + str(buffer_size))
    
    # Process features
    ukmap_features = ukmap.query_features(laqn_buffers, 'buffer_' + str(buffer_size))
    ukmap_features_df = pd.read_sql(ukmap_features.statement, ukmap.engine)

    # Plots
    ax_buffers = london_boundary_df.plot(color = 'r', alpha = 0.2) 
    laqn_buffers_df.plot(ax = ax_buffers, color = 'b')
    plt.show()
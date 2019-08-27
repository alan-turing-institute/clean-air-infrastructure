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

    # Connection for testing
    conn = Connector(secretfile = '.db_inputs_local_secret.json')


    # Import datasources
    laqn = LAQNDatabase(secretfile = '.db_inputs_local_secret.json')

    # Import features 
    london_boundary = LondonBoundary(secretfile = '.db_inputs_local_secret.json')
    london_boundary_df = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement, conn.engine, geom_col='wkb_geometry')
    
    hex_grid = HexGrid(secretfile = '.db_inputs_local_secret.json')
    ukmap = UKMap(secretfile = '.db_inputs_local_secret.json')
    

    # Get interest points
    laqn_buffers = laqn.query_interest_point_buffers([0.001], london_boundary.convex_hull, include_sites=None)
    laqn_buffers_df = geopandas.GeoDataFrame.from_postgis(laqn_buffers.statement, 
                                                          conn.engine, 
                                                          geom_col='buffer_0.001')
    

    ukmap_buffer_intersection = ukmap.query_buffer_intersection(laqn_buffers, 'buffer_0.001')

    generator = ukmap.query_features(ukmap_buffer_intersection)
    gen = list(generator)



    # ukmap_buffer_intersection_df = geopandas.GeoDataFrame.from_postgis(ukmap_buffer_intersection.statement, 
    #                                                       conn.engine, 
    #                                                       geom_col='intersection')


    # ukmap_subquery = ukmap_buffer_intersection.subquery()
    # with conn.open_session() as session:
    #     ukmap_features = session.query(
    #                             ukmap_subquery.c.id,
    #                             ukmap_subquery.c.lat,
    #                             ukmap_subquery.c.lon,
    #                             func.sum(func.ST_Area(ukmap_subquery.c.intersection))
    #                             ).\
    #                         filter(ukmap_subquery.c.feature_type=='Vegetated').\
    #                              group_by(ukmap_subquery.c.id)

    # with conn.open_session() as session:
    #     ukmap_features2 = session.query(
    #                             ukmap_subquery.c.id,
    #                             ukmap_subquery.c.lat,
    #                             ukmap_subquery.c.lon,
    #                             c1(ukmap_subquery.c.intersection)
    #                             ).\
    #                         filter(f1).\
    #                              group_by(ukmap_subquery.c.id)

    
#     with conn.open_session() as session:
#         ints = session.query(buff.c['500'], 
#                              ukmap.table.feature_type,
#                              ukmap.table.shape.label('shape'), 
#                              ukmap.table.objectid.label('objid'), 
#                              buff.c.id.label("buffid"), 
#                              func.ST_Intersection(func.ST_MakeValid(ukmap.table.shape), 
#                                                   buff.c['500']).label("intersection") ).\
#             filter(and_(func.ST_GeometryType(func.ST_MakeValid(ukmap.table.shape))=='ST_MultiPolygon', 
#             func.ST_Intersects(ukmap.table.shape, buff.c['500'])))
    
#     #Extract features
#     ints_subquery = ints.subquery()
#     with conn.open_session() as session:
#         features = session.query(func.sum(func.ST_Area(ints_subquery.c.intersection)),
#                                  ints_subquery.c.buffid).\
#                                  filter(ints_subquery.c.feature_type=='Vegetated').\
#                                  group_by(ints_subquery.c.buffid)


    # Plots
    ax_buffers = london_boundary_df.plot(color = 'r', alpha = 0.2) 
    laqn_buffers_df.plot(ax = ax_buffers, color = 'k')
    plt.show()


    # laqn.query_interest_point_buffers([0.001], london_boundary.convex_hull, include_sites=None, as_dataframe=True)
    
    # hex_interest_points = hex_grid.query_interest_points()
    # laqn_interest_points = laqn.query_interest_points(london_boundary.convex_hull)
    
    # # Get as pandas dataframes for debugging
    # laqn_points = pd.read_sql(laqn_interest_points.statement, conn.engine)
    # hex_points = pd.read_sql(hex_interest_points.statement, conn.engine)


    # # Feature extraction

    # # Get a load of buffers around interest points
    # laqn_buffers = laqn.query_interest_point_buffers(hex_interest_points, [0.001])

        ## Feature Extraction
    # # Set the dates to extract features between
    # start_date = '2019-01-01'
    # end_date = '2019-01-02'

#     # # Make it a sub query
#     # all_interest_points = hex_interest_points.union(laqn_interest_points).subquery()
#     all_interest_points = hex_interest_points.subquery()
#     buff_size = [0.001] #size in m

#     #Get buffers seperately for each interest point source, then Union

#     # Get buffers of different sizes (check teh units of ST_Buffer)
#     query_funcs = [func.ST_Buffer(all_interest_points.c.geom, size).label('500') for size in buff_size]
#     with conn.open_session() as session:
#         buffers = session.query(*query_funcs, all_interest_points.c.id)

#     buff = buffers.subquery()

#     # Get the geometry within an buffer (may not be working properly)
#     with conn.open_session() as session:
#         ints = session.query(buff.c['500'], 
#                              ukmap.table.feature_type,
#                              ukmap.table.shape.label('shape'), 
#                              ukmap.table.objectid.label('objid'), 
#                              buff.c.id.label("buffid"), 
#                              func.ST_Intersection(func.ST_MakeValid(ukmap.table.shape), 
#                                                   buff.c['500']).label("intersection") ).\
#             filter(and_(func.ST_GeometryType(func.ST_MakeValid(ukmap.table.shape))=='ST_MultiPolygon', 
#             func.ST_Intersects(ukmap.table.shape, buff.c['500'])))
    
#     #Extract features
#     ints_subquery = ints.subquery()
#     with conn.open_session() as session:
#         features = session.query(func.sum(func.ST_Area(ints_subquery.c.intersection)),
#                                  ints_subquery.c.buffid).\
#                                  filter(ints_subquery.c.feature_type=='Vegetated').\
#                                  group_by(ints_subquery.c.buffid)

#     features_df = pd.read_sql(features.limit(5).statement, conn.engine)
#     # features_df = geopandas.GeoDataFrame.from_postgis(features.limit(5).statement, conn.engine)


# # #  ['total_museum_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Museum')"],
# # #             ['total_hospital_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Hospitals')"],
# # #             ['total_grass_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Vegetated')"],
# # #             ['total_park_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.landuse='Park' or buffer.landuse='Recreational open space')"],
# # #             ['total_water_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Water')"],
# # #             ['total_flat_area', "sum(ST_Area(buffer.intersected_geom)) filter (where buffer.feature_type='Vegetated' or buffer.feature_type='Water')"],
# # #             ['max_building_height', "max(cast(buffer.calcaulated_height_of_building as float))"],
    
  
# #     # all_ints = pd.read_sql(ints.limit(1000).statement, conn.engine)
# #     london_hull = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement, conn.engine, geom_col='wkb_geometry')
# #     ax = london_hull.plot(color='red', alpha = .2)
# #     all_ints = geopandas.GeoDataFrame.from_postgis(ints.limit(50).statement, 
# #                                                    conn.engine, 
# #                                                    geom_col='intersection')

# #     all_ints2 = geopandas.GeoDataFrame.from_postgis(ints.limit(50).statement, 
# #                                                    conn.engine, 
# #                                                    geom_col='shape')

    
# #     all_ints2.plot(ax = ax, color = 'g', alpha = .3)
# #     all_ints.plot(ax = ax, color = 'g', alpha = 1)
# #     print(all_ints)
# #     plt.show()

# #     # all_ints = ints.all()
# #     # print(len(all_ints))
# #     # plt.plot(*to_shape(buffers.first()[0]).exterior.xy, color = 'r')

# #     # for i in all_ints:
# #     #     plt.plot(*to_shape(i[0]).exterior.xy, color = 'g', alpha = 0.2)

# #     # plt.show()

# #     # buffs = buffers.all()


# # #     REPROCESS_TEMPLATE = """
# # # drop table if exists {schema}.{preprocess_table_name};
# # # select 
# # #    buffers.id,

# # #    {cov_columns},

# # #    ST_Intersection(covs.{cov_geom}, buffers.buffer_geom) as {intersected_geom},
# # #    buffers.buffer_geom,
# # #    buffers.site_geom
# # # into 
# # #    {schema}.{preprocess_table_name}
# # # from
# # #    {schema}.{buffer_table} as buffers,
# # #    {schema}.{covariate_table} as covs
# # # where
# # #    ST_Intersects(covs.{cov_geom}, buffers.buffer_geom);

# # # """

# # # BUFFER_SIZES_DICT = {
# # #     '500': ['500', 0.005], #~500m
# # #     '1000':  ['1c', 0.001], #~1000m
# # #     '100': ['100', 0.0001], #~100m
# # #     '200': ['200', 0.0002] #~200m
# # # }
# # #     # print(len(buffs))
# # #     # # Plot them to check it makes sense (slow)
# # #     # for i, b in enumerate(buffs[:5000]):
# # #     #     print(i)
# # #     #     shapes = [to_shape(b_) for b_ in b]

# # #     #     for s in shapes:
# # #     #         plt.plot(*s.exterior.xy)
    
# # #     # plt.show()

# # #     # TODO:
# #     # 1. Set up ollie code to work with local database
# #     # 2. Figure out how mapping works
# #     # # Get interest points
# #     # hex_interest_points = hex_grid.get_interest_points(start_date, end_date)
# #     # laqn_interest_points = laqn.get_interest_points(london_boundary.convex_hull, start_date, end_date)
    
# #     # with conn.open_session() as session:
# #     #     session.query(func.ST_Buffer(all_interest_points.c.geom, 5.)).all()
    
# #     # interest_points = pd.concat([hex_interest_points, laqn_interest_points])
   
   
# #     # # # Get the points just within that site
# #     # sites_within_boundary = laqn.get_sites_within_geom(london_boundary.convex_hull)
# #     # hex_grid_locs = hex_grid.geom_centroids


# #     # convexhull = lb.convex_hull
# #     # shape = to_shape(WKBElement(convexhull))

# #     # plt.plot(*shape.exterior.xy)
# #     # # plt.show()

    

# #     # for s in sites_within_boundary.all():
# #     #     plt.plot(*(to_shape(s.geom)).xy, 'or')
# #     #     print(s)

# #     # print(pd.read_sql(sites_within_boundary.statement, laqndb.dbcnxn.engine))
# #     # plt.show()

# # # q = s.query(Parent).filter(Parent.child.has(Child.value > 20))
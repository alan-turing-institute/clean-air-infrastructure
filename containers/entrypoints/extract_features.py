"""
Feature extraction
"""

import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers')
import matplotlib.pyplot as plt
from sqlalchemy import insert
import geopandas
from cleanair.features import LondonBoundaryReader, InterestPointReader, UKMapReader
from cleanair.databases import buffer_intersection
import pandas as pd

"""
Run feature extraction
"""
db_info_file = '.db_input_secret_local.json'

start_date = '2019-09-02'
end_date = '2019-09-03'

laqn_include_sites = ["ST4", "LC1", "BT4"]
# laqn_include_sites = None

# Import datasources
# laqn = LAQNReader(secretfile=db_info_file)
# hex_grid = HexGrid(secretfile=db_info_file)

# Import features
ukmap = UKMapReader(secretfile=db_info_file)

# # Import boundary
london_boundary = LondonBoundaryReader(secretfile=db_info_file)

interest_points = InterestPointReader(secretfile=db_info_file)

a = interest_points.query_interest_points(london_boundary.convex_hull)

# # Process interest points
buffer_sizes = [1000, 500, 200, 100, 10]

interest_buffers = interest_points.query_interest_point_buffers(buffer_sizes,
                                                    london_boundary.convex_hull,
                                                    include_sites=None,
                                                    num_seg_quarter_circle=8)

# laqn_readings = laqn.query_interest_point_readings(start_date, end_date,
#                                                     london_boundary.convex_hull,
#                                                     include_sites=laqn_include_sites)

# # Interestpoint buffers create
# Get buffers in decending size order and create column name lists
sorted_buffers = sorted(buffer_sizes)[::-1]
buffer_sizes = [str(s) for s in sorted_buffers]

# # Get buffer intersections
buffer_intersection_query = ukmap.query_buffer_intersection(interest_buffers, buffer_sizes)


# out = pd.read_sql(buffer_intersection_query.limit(10).statement,
#                                                       interest_points.dbcnxn.engine)

# out = geopandas.GeoDataFrame.from_postgis(buffer_intersection_query.limit(10).statement,
#                                                       interest_points.dbcnxn.engine,
#                                                       geom_col = 'intersect_1000')
# print(out)

sel = buffer_intersection_query.subquery().select()

ins = insert(buffer_intersection.IntersectionUKMAP).from_select(['point_id',
                                                                'geographic_type_number',
                                                                'intersect_1000',
                                                                'intersect_500',
                                                                'intersect_200',
                                                                'intersect_100',
                                                                'intersect_10'], sel)


conn = interest_points.dbcnxn.engine.connect()
result = conn.execute(ins)
# # # Process features (Really slow)
# # ukmap_features_df = ukmap.query_features(laqn_buffers, buffer_sizes)
# # ukmap.logger.info("ukmap features processed")

# # # Merge static features with time
# # ukmap_time_features = ukmap.expand_static_feature_df(start_date, end_date, ukmap_features_df)
# # features_with_laqn = ukmap_time_features.merge(laqn_readings, on=['id', 'time'])
# # print(features_with_laqn)

# # # Plot london with laqn buffers
# # london_boundary_df = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement,
# #                                                          london_boundary.engine, geom_col='wkb_geometry')
# ax_buffers = london_boundary_df.plot(color='r', alpha=0.2)
# laqn_buffers_df = geopandas.GeoDataFrame.from_postgis(laqn_buffers.statement,
#                                                       laqn.dbcnxn.engine,
#                                                       geom_col='buffer_' + str(buffer_sizes[0]))
# laqn_buffers_df.plot(ax=ax_buffers, color='b')
# plt.show()


# if __name__ == '__main__':

#     main()

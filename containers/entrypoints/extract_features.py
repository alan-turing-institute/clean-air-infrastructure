"""
UKMap Feature extraction
"""

import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers')

import matplotlib.pyplot as plt

import sqlalchemy 
from sqlalchemy import func, and_, or_, cast, Float
import geopandas
from cleanair.features import LondonBoundaryReader, InterestPointReader, UKMapReader
from cleanair.databases import features_tables


def main()
    # List what sources to process
    sources = ['laqn']

    db_info_file = '.db_input_secret_local.json'

    # Import features
    ukmap = UKMapReader(secretfile=db_info_file)
    london_boundary = LondonBoundaryReader(secretfile=db_info_file)
    interest_points = InterestPointReader(secretfile=db_info_file)


    # # Process interest points (These cannot be chnaged without redfining database schema)
    buffer_sizes = [1000, 500, 200, 100, 10]

    #Check wich interest points have been calculated so we can avoid recalculating
    already_in_features_table = ukmap.feature_interest_points

    interest_buffers = interest_points.query_interest_point_buffers(buffer_sizes,
                                                        london_boundary.convex_hull,
                                                        include_sources=sources,
                                                        exclude_point_ids = already_in_features_table,
                                                        num_seg_quarter_circle=8)

    # Calculate ukmap features and insert into database
    # If having a connection open is a problem you can just repeatedly call the main function,
    # but with a a limit on interest buffers (e.g. interest_buffers.limit(1000))
    # as it only does the calculation for interest points with no features calculated
    ukmap_features_df = ukmap.query_features(interest_buffers, 
                                            buffer_sizes, return_type='insert')



    # print(ukmap_features_df.statement)
    # out = pd.read_sql(ukmap_features_df.limit(1).statement, ukmap.engine)
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


if __name__ == '__main__':

    main()

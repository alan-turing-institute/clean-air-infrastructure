"""
Feature extraction
"""
import matplotlib.pyplot as plt
import geopandas
from datasources import LondonBoundary, LAQNDatabase, UKMap


def main():
    """
    Run feature extraction
    """
    db_info_file = '.db_input_secret_local.json'

    start_date = '2019-09-02'
    end_date = '2019-09-03'

    laqn_include_sites = ["ST4", "LC1", "BT4"]
    # laqn_include_sites = None

    # Import datasources
    laqn = LAQNDatabase(end='today', ndays=2, secretfile=db_info_file)
    # hex_grid = HexGrid(secretfile=db_info_file)

    # Import features
    ukmap = UKMap(secretfile=db_info_file)

    # # Import boundary
    london_boundary = LondonBoundary(secretfile=db_info_file)

    # Process interest points
    buffer_sizes = [1000, 500, 200, 100, 10]
    laqn_buffers = laqn.query_interest_point_buffers(buffer_sizes,
                                                     london_boundary.convex_hull,
                                                     include_sites=laqn_include_sites,
                                                     num_seg_quarter_circle=8)

    laqn_readings = laqn.query_interest_point_readings(start_date, end_date,
                                                       london_boundary.convex_hull,
                                                       include_sites=laqn_include_sites)

    # Process features (Really slow)
    ukmap_features_df = ukmap.query_features(laqn_buffers, buffer_sizes)
    ukmap.logger.info("ukmap features processed")

    # Merge static features with time
    ukmap_time_features = ukmap.expand_static_feature_df(start_date, end_date, ukmap_features_df)
    features_with_laqn = ukmap_time_features.merge(laqn_readings, on=['id', 'time'])
    print(features_with_laqn)

    # Plot london with laqn buffers
    london_boundary_df = geopandas.GeoDataFrame.from_postgis(london_boundary.query_all().statement,
                                                             london_boundary.engine, geom_col='wkb_geometry')
    ax_buffers = london_boundary_df.plot(color='r', alpha=0.2)
    laqn_buffers_df = geopandas.GeoDataFrame.from_postgis(laqn_buffers.statement,
                                                          laqn.dbcnxn.engine,
                                                          geom_col='buffer_' + str(buffer_sizes[0]))
    laqn_buffers_df.plot(ax=ax_buffers, color='b')
    plt.show()


if __name__ == '__main__':

    main()

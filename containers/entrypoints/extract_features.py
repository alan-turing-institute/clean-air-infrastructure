"""
UKMap Feature extraction
"""
import sys
sys.path.append('/Users/jrobinson/Projects/clean-air/clean-air-infrastructure/containers')


import argparse
import logging
from cleanair.loggers import get_log_level

# import sys
# sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers')



import matplotlib.pyplot as plt

import sqlalchemy
from sqlalchemy import func, and_, or_, cast, Float
import geopandas
from cleanair.features import LondonBoundaryReader, InterestPointReader, UKMapReader
from cleanair.databases import features_tables, DBWriter

import time



class FeatureExtractor(DBWriter):
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # kwargs["sources"] = ["aqe"]

        # UKMapExtractor(**kwargs)

        # UKMapExtractor.extract_features()

        # Import features
        self.ukmap = UKMapReader(**kwargs)
        self.london_boundary = LondonBoundaryReader(**kwargs)
        self.interest_points = InterestPointReader(**kwargs)

        # # Process interest points (These cannot be changed without redfining database schema)
        self.buffer_sizes = [1000, 500, 200, 100, 10]



    def extract(self):

        # Check which interest points have been calculated so we can avoid recalculating
        already_in_features_table = self.ukmap.feature_interest_points
        print("already_in_features_table", len(already_in_features_table))

        # interest_buffers = interest_points.query_interest_point_buffers(buffer_sizes,
        #                                                     london_boundary.convex_hull,
        #                                                     include_sources=sources,
        #                                                     exclude_point_ids=already_in_features_table,
        #                                                     )

        q_sensors = self.interest_points.query_locations(self.london_boundary.convex_hull, include_sources=self.sources, exclude_point_ids=already_in_features_table)

        print("sensors sql:", q_sensors)
        # start = time.time()
        # print("sensors", len(q_sensors.all()))
        # print("took:", time.time() - start)

        # for feature_dict in ukmap.features:
            # for column, value in feature_dict.items():
            #     print("column", column, "value", value)

        for q_ukmap in self.ukmap.iterate_features(self.london_boundary.convex_hull):
            print("ukmap sql:", q_ukmap)
            # start = time.time()
            # print("ukmap", len(q_ukmap.all()))
            # print("took:", time.time() - start)

            overlap = self.ukmap.calculate_overlap(q_sensors, q_ukmap, 10)
            print("overlap sql:", overlap)
            start = time.time()
            results = overlap.all()
            for record in results:
                print(record, type(record))
            print("...", len(results))
            print("took:", time.time() - start)

        with self.dbcnxn.open_session() as session:
            site_records = [features_tables.features_UKMAP.build_entry(result) for result in results]
            print("site_records", site_records)
            self.add_records(session, site_records)
            session.commit()

            # ins = insert(features_tables.features_UKMAP).from_select([c.key for c in features_tables.features_UKMAP.__table__.columns], sel)


            # ('aqe', <WKBElement at 0x7f618ee6ee10; 0101000020e6100000d87f9d9b36e3c6bfc284d1ac6cbf4940>, UUID('ad84e264-3e58-439a-ac0e-703d474768e3'), 16004345, datetime.date(2016, 9, 9), 'Hard Standing', 'Nature reserves and sanctuaries', '', 0.0, 0.0, 298.68902646293, 1865.68875002266, <WKBElement at 0x7f618ee6ef10; 01060000a0e6100000010000000103000080010000002200000064e8b900bf6fd2bfae28e280c5c649400000000000000000cc503cc3fa66d2bf47cb874ac3c649400000000000000000fcc928350567d2bfef9b39e1c2c649400000000000000000f84c6a012a67d2bf01cad663c1c6494000000000000000000c0d3a244d67d2bf8e418bfebfc649400000000000000000878d965d4f67d2bf0683bbe8bfc64940000000000000000081dc4ac96a67d2bf4a013adcbec649400000000000000000829b9e877267d2bfb2f4ed81bec649400000000000000000735b40cca267d2bf9d1913a5bcc64940000000000000000000c1216eac67d2bf58619ea7bcc649400000000000000000a8a123486968d2bfea420242bcc649400000000000000000af04a3475069d2bfca5cffc6bbc6494000000000000000004ad95149846ad2bffdbb7a22bbc649400000000000000000b8ce65959f6ad2bf131f517dbac6494000000000000000001229a547c76ad2bf6345ca89bac649400000000000000000727888174d71d2bf869fe32abbc6494000000000000000005cb380ff7671d2bffef54d22bbc649400000000000000000cb20dadb7e71d2bfb8a48822bbc649400000000000000000e39b4a1ffd71d2bf6426402cbbc6494000000000000000002d662e131372d2bfb43c395fb9c6494000000000000000006065879f3b72d2bfefa2df73b4c649400000000000000000784c0aa43c72d2bf74e7963db4c649400000000000000000d3a477369072d2bf55c4cca8acc649400000000000000000a1a5c92da472d2bf55135841a9c649400000000000000000546d1523bb72d2bf51c335e2a8c6494000000000000000007b9e119e1674d2bf9e580d31a6c649400000000000000000d8ae3bba6574d2bf2030817ba7c64940000000000000000080a6601d5274d2bf2fccd2e9a7c649400000000000000000ded4c4719e73d2bf1b5ed7deb1c64940000000000000000069c676184173d2bf5df55890b5c649400000000000000000dd8b0f922072d2bfc28ccac9c2c649400000000000000000ac9f1738f271d2bff494d9c3c5c649400000000000000000d5a382cfed71d2bfa301a60dc6c64940000000000000000064e8b900bf6fd2bfae28e280c5c649400000000000000000>)
            # print("ukmap", len(q_ukmap.all()))


        # # Calculate ukmap features and insert into database
        # # If having a connection open is a problem you can just repeatedly call the main function,
        # # but with a a limit on interest buffers (e.g. interest_buffers.limit(1000))
        # # as it only does the calculation for interest points with no features calculated
        # ukmap_features_df = ukmap.query_features(interest_buffers.limit(10),
        #                                         buffer_sizes, return_type='insert')



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


def main():
    """
    Extract features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get LAQN sensor data")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # List which sources to process
    # sources = ["aqe", "laqn"]
    # sources = ["aqe"]
    kwargs["sources"] = ["aqe"]

    f = FeatureExtractor(**kwargs)
    f.extract()

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print("error:", str(error))
        raise

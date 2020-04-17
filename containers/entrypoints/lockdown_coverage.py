"""
Calculate the coverage for models.
"""
import os
import logging
import numpy as np

from uatraffic.databases import TrafficQuery, TrafficInstanceQuery
from uatraffic.databases import TrafficInstance
from uatraffic.metric import percent_coverage
from uatraffic.preprocess import clean_and_normalise_df
from uatraffic.util import TrafficModelParser

def batch_coverage(instance_df):
    """
    Calculate the coverage using threadings in a batch.
    """

def main():
    """Entrypoint for coverage"""
    # parse arguments from command line
    parser = TrafficModelParser()
    args = parser.parse_args()

    # query objects
    instance_query = TrafficInstanceQuery(secretfile=args.secretfile)
    traffic_query = TrafficQuery(secretfile=args.secretfile)

    # dataframe of instances
    # instance_df = instance_query.get_instances_with_params(output_type="df")
    # print(instance_df.groupby("instance_id").count())

    # filter by detectors
    data_df = instance_query.get_data_config(detectors=args.detectors, output_type="df")
    for _, row in data_df.iterrows():
        assert set(row.to_dict()["data_config"]["detectors"]).issubset(set(args.detectors))

if __name__ == "__main__":
    main()
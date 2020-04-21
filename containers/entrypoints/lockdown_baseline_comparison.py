"""
Calculate the percent of baseline metric for a recent day.
"""

from uatraffic.scoot_processing import TrafficPercentageChange
from uatraffic.parsers import BaselineParser


def main():
    """
    Calculate the percent of baseline metric for a recent day.
    """

    # get args from parser d
    parser = BaselineParser()
    args = parser.parse_args()

    # get query object
    traffic_query = TrafficPercentageChange(
        secretfile=args.secretfile,
        end=args.comparison_end_date,
        nhours=(args.ndays * 24) - 24,
        baseline_tag="normal",
    )

    traffic_query.update_remote_tables()

    traffic_query = TrafficPercentageChange(
        secretfile=args.secretfile,
        end=args.comparison_end_date,
        nhours=(args.ndays * 24) - 24,
        baseline_tag="lockdown",
    )

    traffic_query.update_remote_tables()


if __name__ == "__main__":
    main()

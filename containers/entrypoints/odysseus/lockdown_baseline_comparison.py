"""
Calculate the percent of baseline metric for a recent day.
"""
from datetime import datetime
from dateutil.parser import isoparse
from odysseus.scoot_processing import (
    TrafficPercentageChange,
    LOCKDOWN_BASELINE_END,
    NORMAL_BASELINE_END,
)
from odysseus.parsers import BaselineParser


def main():
    """
    Calculate the percent of baseline metric for a recent day.
    """

    # get args from parser d
    parser = BaselineParser()
    args = parser.parse_args()

    if args.backfill:
        # Calculate how many days are backfillable
        ndays_lockdown = (datetime.today() - isoparse(LOCKDOWN_BASELINE_END)).days
        ndays_normal = (datetime.today() - isoparse(NORMAL_BASELINE_END)).days

        # get query object
        traffic_query_normal = TrafficPercentageChange(
            secretfile=args.secretfile,
            end=args.comparison_end_date,
            nhours=(ndays_normal * 24) - 24,
            baseline_tag="normal",
        )

        traffic_query_lockdown = TrafficPercentageChange(
            secretfile=args.secretfile,
            end=args.comparison_end_date,
            nhours=(ndays_lockdown * 24) - 24,
            baseline_tag="lockdown",
        )

    else:

        # get query object
        traffic_query_normal = TrafficPercentageChange(
            secretfile=args.secretfile,
            end=args.comparison_end_date,
            nhours=(args.ndays * 24) - 24,
            baseline_tag="normal",
        )

        traffic_query_lockdown = TrafficPercentageChange(
            secretfile=args.secretfile,
            end=args.comparison_end_date,
            nhours=(args.ndays * 24) - 24,
            baseline_tag="lockdown",
        )

    traffic_query_lockdown.update_remote_tables()
    traffic_query_normal.update_remote_tables()


if __name__ == "__main__":
    main()

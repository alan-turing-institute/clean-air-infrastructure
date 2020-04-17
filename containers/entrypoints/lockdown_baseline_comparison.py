"""
Calculate the percent of baseline metric for a recent day.
"""

from uatraffic.scoot_processing import TrafficPercentageChange
from uatraffic.parsers import BaselineParser

NORMAL_BASELINE_START = "2020-02-10"
NORMAL_BASELINE_END = "2020-03-03"
LOCKDOWN_BASELINE_START = "2020-02-10"
LOCKDOWN_BASELINE_END = "2020-04-13"


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
        baseline_start=NORMAL_BASELINE_START,
        baseline_end=NORMAL_BASELINE_END,
    )

    traffic_query.update_remote_tables()

    traffic_query = TrafficPercentageChange(
        secretfile=args.secretfile,
        end=args.comparison_end_date,
        nhours=(args.ndays * 24) - 24,
        baseline_tag="lockdown",
        baseline_start=NORMAL_BASELINE_START,
        baseline_end=NORMAL_BASELINE_END,
    )

    traffic_query.update_remote_tables()


if __name__ == "__main__":
    main()

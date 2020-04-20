from flask import Blueprint
from webargs import fields
from webargs.flaskparser import use_args
from ..queries import ScootDaily, ScootDailyPerc, ScootHourly
from ..db import get_session
from ..argparsers import validate_today_or_before, validate_iso_string


scoot_bp = Blueprint("scoot", __name__)


time_args_dict = {
    "starttime": fields.String(required=True, validate=validate_iso_string),
    "endtime": fields.String(required=False, validate=validate_today_or_before),
}


@scoot_bp.route("hourly/raw", methods=["GET"])
@use_args(
    time_args_dict, location="query",
)
def scoot(args):
    """Get scoot data with lat and lon between start_time and end_time.

    Streams the results from the database and uses yeild_per to avoid loading all data into memory

    Example:
    To request forecast at all points within a bounding box over city hall
    pip install httpie
    http --download GET :5000/api/v1/scoot/hourly/raw starttime=='2020-03-01' endtime=='2020-03-02'
    http --download GET urbanair.turing.ac.uk/api/v1/scoot/hourly/raw starttime=='2020-03-01' endtime=='2020-03-02'
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)

    db_query = ScootHourly()

    return db_query.stream_csv(
        "scoot_hourly", get_session(), start_time=starttime, end_time=endtime
    )


@scoot_bp.route("daily/raw", methods=["GET"])
@use_args(
    time_args_dict, location="query",
)
def scoot_daily(args):
    """Get scoot data with lat and lon between start_time and end_time.

    Streams the results from the database and uses yeild_per to avoid loading all data into memory

    Example:
    To request forecast at all points within a bounding box over city hall
    pip install httpie
    http --download GET :5000/api/v1/scoot/daily/raw starttime=='2020-03-01' endtime=='2020-03-02'
    http --download GET urbanair.turing.ac.uk/api/v1/scoot/daily/raw starttime=='2020-03-01' endtime=='2020-03-02'
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)

    db_query = ScootDaily()

    return db_query.stream_csv(
        "scoot_daily", get_session(), start_time=starttime, end_time=endtime
    )


@scoot_bp.route("daily/percent-of-baseline", methods=["GET"])
@use_args(
    {
        **time_args_dict,
        **{
            "baseline": fields.String(
                required=True, validate=lambda val: val in ["lockdown", "normal"]
            ),
            "exclude_baseline_no_traffic": fields.Bool(missing="true"),
            "exclude_comparison_no_traffic": fields.Bool(missing="true"),
            "exclude_low_confidence": fields.Bool(missing="true"),
            "return_meta": fields.Bool(missing="true"),
        },
    },
    location="query",
)
def scoot_percentage(args):
    """
    Return scoot data as a percentage of a baseline
    This is using docstrings for specifications.
    ---
    parameters:
      - name: starttime
        in: query
        type: string
        required: true
        description: ISO date. Request data from this date
      - name: endtime
        in: query
        type: string
        required: true
        description: ISO date. Request data until (but excluding) this date 
      - name: baseline
        in: query
        type: string
        enum: ['lockdown', 'normal']
        required: true
        description: Use the 'lockdown' or 'normal' period for comparison
      - name: exclude_baseline_no_traffic
        in: query
        type: boolean
        default: true
        description: Exclude any rows which have no data in baseline period
      - name: exclude_comparison_no_traffic
        in: query
        type: boolean
        default: true
        description: Exclude any rows which have no data in comparison period
      - name: exclude_low_confidence
        in: query
        type: boolean
        default: true
        description: Exclude any rows which have low confidence
      - name: return_meta
        in: query
        type: boolean
        default: true
        description: Return metadata columns
    responses:
      200:
        description: A csv file containing the data
        content:  # Response body
            application/csv
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)
    baseline = args.pop("baseline")
    exclude_baseline_no_traffic = args.pop("exclude_baseline_no_traffic")
    exclude_comparison_no_traffic = args.pop("exclude_comparison_no_traffic")
    exclude_low_confidence = args.pop("exclude_low_confidence")
    return_meta = args.pop("return_meta")

    db_query = ScootDailyPerc()

    return db_query.stream_csv(
        "scoot_daily_percentage",
        get_session(),
        starttime,
        endtime,
        baseline,
        exclude_baseline_no_traffic,
        exclude_comparison_no_traffic,
        exclude_low_confidence,
        return_meta,
    )

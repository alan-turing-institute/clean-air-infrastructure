from flask import Blueprint
from webargs import fields
from webargs.flaskparser import use_args
from uatraffic.scoot_processing import (
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
    NORMAL_BASELINE_START,
    NORMAL_BASELINE_END,
)
from ..queries import ScootDaily, ScootDailyPerc, ScootHourly
from ..db import get_session
from ..argparsers import (
    validate_today_or_before,
    validate_iso_string,
    validate_lockdown_date,
)

# Create a Blueprint
scoot_bp = Blueprint("scoot", __name__)


# Query objects
scoot_daily_percent = ScootDailyPerc()


@scoot_bp.route("hourly/raw", methods=["GET"])
@use_args(
    {
        "starttime": fields.String(required=True, validate=validate_iso_string),
        "endtime": fields.String(required=False, validate=validate_today_or_before),
    },
    location="query",
)
def scoot(args):
    """
    Return raw hourly scoot data
    Return raw hourly scoot data.
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
        description: ISO date. Request data until (but excluding) this date 
    responses:
      200:
        description: A csv file containing the data
        content:  # Response body
            application/json
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)

    db_query = ScootHourly()

    return db_query.stream_csv(
        "scoot_hourly", get_session(), start_time=starttime, end_time=endtime
    )


@scoot_bp.route("daily/raw", methods=["GET"])
@use_args(
    {
        "starttime": fields.String(required=True, validate=validate_iso_string),
        "endtime": fields.String(required=False, validate=validate_today_or_before),
    },
    location="query",
)
def scoot_daily(args):
    """
    Return daily scoot data
    Return scoot data averaged over days
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
        description: ISO date. Request data until (but excluding) this date 
    responses:
      200:
        description: A csv file containing the data
        content:  # Response body
            application/json
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)

    db_query = ScootDaily()

    return db_query.stream_csv(
        "scoot_daily", get_session(), start_time=starttime, end_time=endtime
    )


@scoot_bp.route("daily/percent-of-baseline/lockdown", methods=["GET"])
@use_args(
    {
        "starttime": fields.String(
            required=True,
            validate=lambda val: validate_lockdown_date(val, LOCKDOWN_BASELINE_END),
        ),
        "endtime": fields.String(
            required=False, validate=lambda val: validate_today_or_before(val),
        ),
        "exclude_baseline_no_traffic": fields.Bool(missing="true"),
        "exclude_comparison_no_traffic": fields.Bool(missing="true"),
        "exclude_low_confidence": fields.Bool(missing="true"),
        "return_meta": fields.Bool(missing="true"),
    },
    location="query",
)
def scoot_percentage_lockdown(args):
    """
    Return scoot data as a percentage of a 'lockdown' baseline
    Return scoot data as a percentage of a 'lockdown' baseline.
    ---
    parameters:
      - name: starttime
        in: query
        type: string
        required: true
        description: ISO date. Request data from this date. Must be '2020-04-20' or later.
      - name: endtime
        in: query
        type: string
        description: ISO date. Request data until (but excluding) this date. If not provided will return all available data from starttime
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
        description: Exclude any rows which have less than 6 hours of data matched between baseline and comparison
      - name: return_meta
        in: query
        type: boolean
        default: true
        description: Return metadata columns. 
    responses:
      200:
        description: A csv file containing the data
        content:  # Response body
            application/json
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)
    baseline = "lockdown"
    exclude_baseline_no_traffic = args.pop("exclude_baseline_no_traffic")
    exclude_comparison_no_traffic = args.pop("exclude_comparison_no_traffic")
    exclude_low_confidence = args.pop("exclude_low_confidence")
    return_meta = args.pop("return_meta")

    return scoot_daily_percent.stream_csv(
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


@scoot_bp.route("daily/percent-of-baseline/normal", methods=["GET"])
@use_args(
    {
        "starttime": fields.String(
            required=True,
            validate=lambda val: validate_lockdown_date(val, NORMAL_BASELINE_END),
        ),
        "endtime": fields.String(
            required=False, validate=lambda val: validate_today_or_before(val),
        ),
        "exclude_baseline_no_traffic": fields.Bool(missing="true"),
        "exclude_comparison_no_traffic": fields.Bool(missing="true"),
        "exclude_low_confidence": fields.Bool(missing="true"),
        "return_meta": fields.Bool(missing="true"),
    },
    location="query",
)
def scoot_percentage(args):
    """
    Return scoot data as a percentage of a 'normal' baseline
    Return scoot data as a percentage of a 'normal' baseline. In the returned csv Monday=0
    ---
    parameters:
      - name: starttime
        in: query
        type: string
        required: true
        description: ISO date.  Request data from this date. Must be '2020-03-02' or later.
      - name: endtime
        in: query
        type: string
        description: ISO date. Request data until (but excluding) this date. If not provided will return all available data from starttime
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
        description: Exclude any rows which have less than 6 hours of data matched between baseline and comparison
      - name: return_meta
        in: query
        type: boolean
        default: true
        description: Return metadata columns. 
    responses:
      200:
        description: A csv file containing the data
        content:  # Response body
            application/json
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)
    baseline = "normal"
    exclude_baseline_no_traffic = args.pop("exclude_baseline_no_traffic")
    exclude_comparison_no_traffic = args.pop("exclude_comparison_no_traffic")
    exclude_low_confidence = args.pop("exclude_low_confidence")
    return_meta = args.pop("return_meta")

    return scoot_daily_percent.stream_csv(
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

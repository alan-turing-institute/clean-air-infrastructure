from flask import Blueprint
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort
from ..queries import ScootDaily, ScootDailyPerc, ScootHourly
from ..db import get_session


scoot_bp = Blueprint('scoot', __name__)


@scoot_bp.route('/hourly/raw', methods=['GET'])
@use_args(
    {
        "starttime": fields.String(required=True),
        "endtime": fields.String(required=False),
    },
    location="query",
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


@scoot_bp.route("/daily/raw", methods=["GET"])
@use_args(
    {
        "starttime": fields.String(required=True),
        "endtime": fields.String(required=False),
        "output":  fields.String(required=False, validate=lambda val: val in ["json", "csv"]),
    },
    location="query",
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
        "starttime": fields.String(required=True),
        "endtime": fields.String(required=False),
        "baseline": fields.String(
            required=True, validate=lambda val: val in ["lockdown", "normal"]
        ),
    },
    location="query",
)
def scoot_percentage(args):
    """Get scoot percentage data

    http --download GET :5000/api/v1/scoot/daily/percent-of-baseline starttime=='2020-03-01' endtime=='2020-03-02' baseline=='normal'
    http --download GET urbanair.turing.ac.uk/api/v1/scoot/daily/percent-of-baseline starttime=='2020-03-01' endtime=='2020-03-02' baseline=='normal'
    """

    starttime = args.pop("starttime")
    endtime = args.pop("endtime", None)
    baseline = args.pop("baseline")

    db_query = ScootDailyPerc()

    return db_query.stream_csv(
        "scoot_daily_percentage",
        get_session(),
        baseline,
        start_time=starttime,
        end_time=endtime
    )

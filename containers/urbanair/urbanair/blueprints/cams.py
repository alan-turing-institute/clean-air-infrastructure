from flask import Blueprint, g, jsonify
from webargs import fields
from webargs.flaskparser import use_args
import json
from ..queries import CamRecent, CamsSnapshot
from ..db import get_session

# Create a Blueprint
cams_bp = Blueprint("cams", __name__)


@cams_bp.route("recent", methods=["GET"])
@use_args(
    {"id": fields.String(required=True),}, location="query",
)
def cam_recent(args):
    """
    Return raw historical count per camera
    ---
    parameters:
      - name: camera_id
        in: query
        type: string
        required: true
        description: Camera ID, in jamcam format
    responses:
      200:
        description: A JSON containing historical counts
        content:  # Response body
            application/json
    """

    db_query = CamRecent()

    return db_query.response_json(get_session(), id=args.pop("id"))


@cams_bp.route("snapshot", methods=["GET"])
@use_args(
    {"type": fields.String(required=True),}, location="query",
)
def cams_snapshot(args):
    """
    Return raw historical count per camera
    ---
    responses:
      200:
        description: A JSON containing last hour of aggregated count data per camera
        content:  # Response body
            application/json
    """

    db_query = CamsSnapshot()

    return db_query.response_json(get_session(), type=args.pop("type"))

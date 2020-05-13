from flask import Blueprint, Response, render_template
from ..auth import http_auth

static_bp = Blueprint("index", __name__)

@static_bp.route("/", methods=["GET"])
@http_auth.login_required
def index():
    return render_template('index.html')

@static_bp.route("/mapjam", methods=["GET"])
@http_auth.login_required
def map():
    return render_template('map.html')
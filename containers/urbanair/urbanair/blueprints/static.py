from flask import Blueprint, Response, render_template

static_bp = Blueprint("index", __name__)

@static_bp.route("/", methods=["GET"])
def index():
    return render_template('index.html')

@static_bp.route("/map", methods=["GET"])
def map():
    return render_template('map.html')
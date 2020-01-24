"""
The main plotly dashboard.

Inspired by https://dash.plot.ly/interactive-graphing

"""

from . import timeseries
from . import layout
from .. import util

def main():
    app = layout.get_base_layout()
    print("Served at: http://127.0.0.1:8050")
    app.run_server(debug=True)

if __name__ == "__main__":
    main()

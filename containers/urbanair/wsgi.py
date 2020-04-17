"""Run the flask app"""
from urbanair import create_app
# pylint: disable=C0103
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

""" 
An API to get cleanair data
"""

from flask import Flask, jsonify, request, abort

app = Flask(__name__)


@app.route('/')
def get_info():
    return jsonify({'Info': 'Welcome to the CleanAir API'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
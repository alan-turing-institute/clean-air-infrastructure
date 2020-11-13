import requests


def get_tomtom_data(zoom: int, x: int, y: int):
	key = ''
	return requests.get(f'https://api.tomtom.com/traffic/map/4/tile/flow/absolute/{zoom}/{x}/{y}.png?key={key}&tileSize=512').content

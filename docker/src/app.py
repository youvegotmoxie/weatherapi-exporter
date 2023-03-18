import requests, os
from flask import Flask, redirect, request
from prometheus_client import Gauge, Info, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

apiBaseUrl = "https://api.weatherapi.com/v1"
apiEndpoint = "current.json"
apiKey = os.environ.get('API_KEY')

app = Flask(__name__)

# TODO: make this not shit
curTemp = Gauge("current_temperature", "Current temperature in F", labelnames=['city', 'state'])
curWindSpeed = Gauge("current_wind_speed", "Current wind speed in MPH", labelnames=['city', 'state'])
curWindDir = Gauge("current_wind_direction", "Current wind direction in degrees", labelnames=['city', 'state'])
curPrecip = Gauge("current_precipitation", "Current precipitation levels in inches", labelnames=['city', 'state'])
curHumid = Gauge("current_humidity", "Current humidity level", labelnames=['city', 'state'])
curUV = Gauge("current_uv_index", "Current UV index", labelnames=['city', 'state'])
wInfo = Info('current_weather_all', 'Full weather details for location')

@app.route("/", methods=['GET'])
def root():
  return {"status": "ok"}

@app.route("/weather/<location>", methods=['GET'])
def get_weather(location: str):
  raw_header = request.headers.get('X-WAPI-RAW', False)
  apiQuery = f"{apiBaseUrl}/{apiEndpoint}?key={apiKey}&q={location}&aqi=yes"
  request = requests.get(apiQuery)
  requestBody = request.json()

  area_info = {
    "city": f"{requestBody['location']['name']}",
    "state": f"{requestBody['location']['region']}"
  }

  weather_info = {
    "temp": f"{requestBody['current']['temp_f']}",
    "wind_speed": f"{requestBody['current']['wind_mph']}",
    "wind_direction": f"{requestBody['current']['wind_degree']}",
    "sky_conditions": f"{requestBody['current']['condition']['text']}",
    "humidity": f"{requestBody['current']['humidity']}",
    "precipitation": f"{requestBody['current']['precip_in']}",
    "cloud_cover": f"{requestBody['current']['cloud']}",
    "uv_index": f"{requestBody['current']['uv']}",
    "visibility": f"{requestBody['current']['vis_miles']}"
  }

  city, state = area_info['city'], area_info['state']

  # TODO: make this not shit
  curTemp.labels(city, state).set(weather_info['temp'])
  curWindSpeed.labels(city, state).set(weather_info['wind_speed'])
  curWindDir.labels(city, state).set(weather_info['wind_direction'])
  curPrecip.labels(city, state).set(weather_info['precipitation'])
  curHumid.labels(city, state).set(weather_info['humidity'])
  curUV.labels(city, state).set(weather_info['uv_index'])

  area_info.update(weather_info)
  wInfo.info(area_info)

  if raw_header is True:
    return area_info
  else:
    return redirect("/metrics")

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})

if __name__ == '__main__':
  app.run()

import requests, os, json
from collections import namedtuple
from flask import Flask, redirect
from flask import request as flask_request
from prometheus_client import Gauge, Info, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

apiBaseUrl = "https://api.weatherapi.com/v1"
apiEndpoint = "current.json"
apiKey = os.environ.get('API_KEY')

prometheus_labels = ['city', 'state']

app = Flask(__name__)

class ObjectConvert(object):
    def __init__(self, input_dict: dict) -> None:
        self.__dict__.update(input_dict)

# TODO: make this not shit
curTemp = Gauge("current_temperature", "Current temperature in F", labelnames=prometheus_labels)
curWindSpeed = Gauge("current_wind_speed", "Current wind speed in MPH", labelnames=prometheus_labels)
curWindDir = Gauge("current_wind_direction", "Current wind direction in degrees", labelnames=prometheus_labels)
curPrecip = Gauge("current_precipitation", "Current precipitation levels in inches", labelnames=prometheus_labels)
curHumid = Gauge("current_humidity", "Current humidity level", labelnames=prometheus_labels)
curUV = Gauge("current_uv_index", "Current UV index", labelnames=prometheus_labels)
curCloud = Gauge("current_cloud_cover", "Current Level of cloud cover", labelnames=prometheus_labels)
curPressure = Gauge("current_baro_pressure", "Current barometric pressure", labelnames=prometheus_labels)
wInfo = Info('current_weather_all', 'Full weather details for location')

@app.route("/", methods=['GET'])
def root():
  if os.path.exists('/proc/uptime'):
    with open('/proc/uptime', 'r') as up:
      uptime = up.read()
    return {"status": "ok", "uptime": f"{uptime.split(' ')[0]}"}
  else:
    return {"status": "ok"}

@app.route("/weather/<location>", methods=['GET'])
def get_weather(location: str):
  wapi_custom_headers = flask_request.headers.get('X-WAPI-Custom', None)

  apiQuery = f"{apiBaseUrl}/{apiEndpoint}?key={apiKey}&q={location}&aqi=no"
  request = requests.get(apiQuery)
  requestBody = json.loads(request.text, object_hook=ObjectConvert)

  area_info = {
    "city": f"{requestBody.location.name}",
    "state": f"{requestBody.location.region}"
  }

  weather_info = {
    "temp": f"{requestBody.current.temp_f}",
    "wind_speed": f"{requestBody.current.wind_mph}",
    "wind_direction": f"{requestBody.current.wind_degree}",
    "sky_conditions": f"{requestBody.current.condition.text}",
    "humidity": f"{requestBody.current.humidity}",
    "precipitation": f"{requestBody.current.precip_in}",
    "cloud_cover": f"{requestBody.current.cloud}",
    "uv_index": f"{requestBody.current.uv}",
    "visibility": f"{requestBody.current.vis_miles}",
    "pressure": f"{requestBody.current.pressure_in}"
  }

  city, state = area_info['city'], area_info['state']

  area_info.update(weather_info)

  match wapi_custom_headers:
    case "raw":
      return area_info

  # TODO: make this not shit
  curTemp.labels(city, state).set(weather_info['temp'])
  curWindSpeed.labels(city, state).set(weather_info['wind_speed'])
  curWindDir.labels(city, state).set(weather_info['wind_direction'])
  curPrecip.labels(city, state).set(weather_info['precipitation'])
  curHumid.labels(city, state).set(weather_info['humidity'])
  curUV.labels(city, state).set(weather_info['uv_index'])
  curCloud.labels(city, state).set(weather_info['cloud_cover'])
  curPressure.labels(city, state).set(weather_info['pressure'])
  wInfo.info(area_info)

  return redirect("/metrics")


app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})

if __name__ == '__main__':
  app.run()

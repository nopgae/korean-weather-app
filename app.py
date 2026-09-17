"""
Korean City Weather Monitor
Flask web app + REST API using Open-Meteo (no API key required)
"""

from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Major Korean cities with coordinates
CITIES = {
    "Seoul":    {"lat": 37.5665, "lon": 126.9780},
    "Busan":    {"lat": 35.1796, "lon": 129.0756},
    "Incheon":  {"lat": 37.4563, "lon": 126.7052},
    "Daegu":    {"lat": 35.8714, "lon": 128.6014},
    "Daejeon":  {"lat": 36.3504, "lon": 127.3845},
    "Gwangju":  {"lat": 35.1595, "lon": 126.8526},
    "Suwon":    {"lat": 37.2636, "lon": 127.0286},
    "Jeju":     {"lat": 33.4996, "lon": 126.5312},
}

# WMO weather code descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Heavy rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def get_weather(city_name):
    city = CITIES.get(city_name)
    if not city:
        return {"error": f"City '{city_name}' not found"}

    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature,precipitation",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data["current"]
        daily = data["daily"]
        return {
            "city": city_name,
            "temperature": current["temperature_2m"],
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "precipitation": current["precipitation"],
            "condition": WMO_CODES.get(current["weather_code"], "Unknown"),
            "temp_max": daily["temperature_2m_max"][0],
            "temp_min": daily["temperature_2m_min"][0],
        }
    except requests.RequestException as e:
        return {"city": city_name, "error": str(e)}


@app.route("/")
def index():
    weather_data = [get_weather(city) for city in CITIES]
    return render_template("index.html", cities=weather_data)


@app.route("/api/weather")
def api_all():
    """GET /api/weather — returns weather for all cities as JSON"""
    return jsonify([get_weather(city) for city in CITIES])


@app.route("/api/weather/<city_name>")
def api_city(city_name):
    """GET /api/weather/<city_name> — returns weather for one city"""
    return jsonify(get_weather(city_name.capitalize()))


if __name__ == "__main__":
    app.run(debug=False, port=5000)

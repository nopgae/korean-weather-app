"""
Korean City Weather Monitor
Flask web app + REST API using Open-Meteo (no API key required)
"""

import os
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, jsonify
import requests
from sqlalchemy import (Column, DateTime, Float, Integer, MetaData, String, Table,
                        create_engine, func, insert, select)

app = Flask(__name__)

# Azure PostgreSQL in the cloud (DATABASE_URL), local SQLite file otherwise
db_url = os.environ.get("DATABASE_URL", "sqlite:///weather.db")
db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)  # use psycopg 3 driver
engine = create_engine(db_url, pool_pre_ping=True)
metadata = MetaData()
readings = Table(
    "readings", metadata,
    Column("id", Integer, primary_key=True),
    Column("city", String(32), index=True, nullable=False),
    Column("temperature", Float),
    Column("humidity", Float),
    Column("wind_speed", Float),
    Column("condition", String(64)),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
)
metadata.create_all(engine)

SAVE_INTERVAL = timedelta(minutes=10)  # avoid one row per page refresh

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


def save_readings(weather_data):
    """Store one reading per city, at most once per SAVE_INTERVAL."""
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        last = conn.execute(select(func.max(readings.c.recorded_at))).scalar()
        if last is not None and last.tzinfo is None:  # SQLite drops tzinfo
            last = last.replace(tzinfo=timezone.utc)
        if last and now - last < SAVE_INTERVAL:
            return
        rows = [{k: w[k] for k in ("city", "temperature", "humidity", "wind_speed", "condition")}
                | {"recorded_at": now} for w in weather_data if "error" not in w]
        if rows:
            conn.execute(insert(readings), rows)


def get_history(city_name, limit=200):
    with engine.connect() as conn:
        rows = conn.execute(
            select(readings.c.temperature, readings.c.humidity, readings.c.recorded_at)
            .where(readings.c.city == city_name)
            .order_by(readings.c.recorded_at.desc()).limit(limit)
        ).all()
    return [{"temperature": r.temperature, "humidity": r.humidity,
             "recorded_at": (r.recorded_at if r.recorded_at.tzinfo else r.recorded_at.replace(tzinfo=timezone.utc)).isoformat()}
            for r in reversed(rows)]


@app.route("/")
def index():
    weather_data = [get_weather(city) for city in CITIES]
    save_readings(weather_data)
    with engine.connect() as conn:
        total = conn.execute(select(func.count()).select_from(readings)).scalar()
    return render_template("index.html", cities=weather_data, total=total)


@app.route("/history/<city_name>")
def history_page(city_name):
    name = city_name.capitalize()
    if name not in CITIES:
        return "City not found", 404
    return render_template("history.html", city=name, history=get_history(name))


@app.route("/api/history/<city_name>")
def api_history(city_name):
    """GET /api/history/<city_name> — stored readings for one city (oldest first)"""
    name = city_name.capitalize()
    if name not in CITIES:
        return jsonify({"error": f"City '{city_name}' not found", "cities": list(CITIES)}), 404
    return jsonify(get_history(name))


@app.route("/api/health")
def health():
    with engine.connect() as conn:
        conn.execute(select(1))
    return jsonify(status="ok", db=engine.dialect.name)


@app.route("/api/weather")
def api_all():
    """GET /api/weather — returns weather for all cities as JSON"""
    return jsonify([get_weather(city) for city in CITIES])


@app.route("/api/weather/<city_name>")
def api_city(city_name):
    """GET /api/weather/<city_name> — returns weather for one city"""
    name = city_name.capitalize()
    if name not in CITIES:
        return jsonify({"error": f"City '{city_name}' not found", "cities": list(CITIES)}), 404
    data = get_weather(name)
    return jsonify(data), 502 if "error" in data else 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8000)

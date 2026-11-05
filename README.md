# Korean City Weather Monitor

A Flask web application that displays real-time weather for 8 major Korean cities and exposes a clean REST API. Uses the [Open-Meteo](https://open-meteo.com) API — completely free, no API key required.

## Features

- Live weather dashboard for Seoul, Busan, Incheon, Daegu, Daejeon, Gwangju, Suwon, and Jeju
- REST API endpoints returning structured JSON
- Weather data: temperature, feels-like, humidity, wind speed, precipitation, daily high/low
- No API key needed — built on Open-Meteo's free public API
- **Database-backed history**: each dashboard load stores one reading per city (at most every 10 min) → per-city temperature/humidity chart
- Runs on SQLite locally and **Azure Database for PostgreSQL** in the cloud (set `DATABASE_URL`)

## Tech Stack

- **Backend:** Python 3, Flask, SQLAlchemy Core
- **Database:** SQLite (local) / Azure Database for PostgreSQL (psycopg 3)
- **Deploy:** Azure VM (gunicorn) and Azure App Service (Linux, Python)
- **Data:** Open-Meteo REST API (free, no auth)
- **Frontend:** Jinja2 templates, plain HTML/CSS (responsive grid)
- **HTTP client:** requests

## Project Structure

```
.
├── app.py                # Flask app + API routes
├── templates/
│   ├── index.html        # Weather dashboard UI
│   └── history.html      # Per-city history chart (Chart.js)
├── test_app.py           # API status-code tests (pytest)
├── requirements.txt
└── README.md
```

## How to Run

```bash
pip install -r requirements.txt
python app.py                          # SQLite file weather.db
```

Then open [http://localhost:8000](http://localhost:8000).

To use PostgreSQL, set `DATABASE_URL` (Azure requires SSL):

```bash
export DATABASE_URL="postgresql://<user>:<password>@<server>.postgres.database.azure.com:5432/postgres?sslmode=require"
gunicorn -b 0.0.0.0:8000 app:app
```

The `readings` table is created automatically on startup.

Run the tests (offline, no network calls):

```bash
pip install pytest
pytest -q
```

## API Reference

| Endpoint | Description |
|---|---|
| `GET /` | HTML weather dashboard |
| `GET /api/weather` | All cities as JSON array |
| `GET /api/weather/<city>` | Single city (e.g., `Seoul`, `Busan`, `Jeju`). Unknown city → `404`; upstream API failure → `502` |
| `GET /history/<city>` | HTML chart of stored readings |
| `GET /api/history/<city>` | Stored readings from the DB (oldest first, last 200) |
| `GET /api/health` | App + DB connectivity check |

**Example response** (`GET /api/weather/Seoul`):
```json
{
  "city": "Seoul",
  "temperature": 3.5,
  "feels_like": -1.2,
  "humidity": 63,
  "wind_speed": 11.9,
  "precipitation": 0.0,
  "condition": "Partly cloudy",
  "temp_max": 6.1,
  "temp_min": -1.4
}
```

## Limitations

- Each page load makes 8 sequential Open-Meteo calls with no caching, so page loads are slow and would hit rate limits under real traffic.
- Readings are only recorded when someone opens the dashboard (no background scheduler).

## Relevance to Data Science / SCM Roles

- REST API design and consumption — common in production data pipelines
- Weather data integration applicable to demand forecasting (weather-sensitive SKUs, logistics routing)
- Flask as a lightweight model-serving or data service layer

---

*Inspired by a Naver Weather scraping prototype; rebuilt on a stable public API with full web UI and REST endpoints.*

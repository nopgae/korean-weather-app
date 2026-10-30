# Korean City Weather Monitor

A Flask web application that displays real-time weather for 8 major Korean cities and exposes a clean REST API. Uses the [Open-Meteo](https://open-meteo.com) API — completely free, no API key required.

## Features

- Live weather dashboard for Seoul, Busan, Incheon, Daegu, Daejeon, Gwangju, Suwon, and Jeju
- REST API endpoints returning structured JSON
- Weather data: temperature, feels-like, humidity, wind speed, precipitation, daily high/low
- No API key needed — built on Open-Meteo's free public API

## Tech Stack

- **Backend:** Python 3, Flask
- **Data:** Open-Meteo REST API (free, no auth)
- **Frontend:** Jinja2 templates, plain HTML/CSS (responsive grid)
- **HTTP client:** requests

## Project Structure

```
.
├── app.py                # Flask app + API routes
├── templates/
│   └── index.html        # Weather dashboard UI
├── test_app.py           # API status-code tests (pytest)
├── requirements.txt
└── README.md
```

## How to Run

```bash
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000](http://localhost:5000). On macOS, port 5000 may be taken by AirPlay Receiver; turn it off in System Settings or change the port in `app.py`.

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
- Uses Flask's development server; not set up for production deployment.

## Relevance to Data Science / SCM Roles

- REST API design and consumption — common in production data pipelines
- Weather data integration applicable to demand forecasting (weather-sensitive SKUs, logistics routing)
- Flask as a lightweight model-serving or data service layer

---

*Inspired by a Naver Weather scraping prototype; rebuilt on a stable public API with full web UI and REST endpoints.*

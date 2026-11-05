from unittest.mock import patch

from app import app


def test_unknown_city_returns_404() -> None:
    r = app.test_client().get("/api/weather/Atlantis")
    assert r.status_code == 404
    assert "Seoul" in r.get_json()["cities"]


def test_upstream_failure_returns_502() -> None:
    with patch("app.get_weather", return_value={"city": "Seoul", "error": "timeout"}):
        r = app.test_client().get("/api/weather/seoul")
    assert r.status_code == 502


FAKE = {"city": "Seoul", "temperature": 12.5, "feels_like": 11.0, "humidity": 60,
        "wind_speed": 5.0, "precipitation": 0, "condition": "Clear sky", "temp_max": 15, "temp_min": 8}


def test_dashboard_saves_reading_and_history_returns_it(tmp_path, monkeypatch) -> None:
    import app as appmod
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{tmp_path}/t.db")
    appmod.metadata.create_all(engine)
    monkeypatch.setattr(appmod, "engine", engine)
    with patch("app.get_weather_many", side_effect=lambda cs: [FAKE | {"city": c} for c in cs]):
        client = app.test_client()
        assert client.get("/").status_code == 200
        client.get("/")  # second load within 10 min must not duplicate rows
    h = client.get("/api/history/seoul").get_json()
    assert len(h) == 1 and h[0]["temperature"] == 12.5
    assert client.get("/history/Seoul").status_code == 200
    assert client.get("/api/health").get_json()["db"] == "sqlite"


def test_get_weather_many_maps_list_response_in_order() -> None:
    import app as appmod
    loc = lambda t: {"current": {"temperature_2m": t, "apparent_temperature": t, "relative_humidity_2m": 50,
                                 "wind_speed_10m": 1, "precipitation": 0, "weather_code": 0},
                     "daily": {"temperature_2m_max": [t + 1], "temperature_2m_min": [t - 1]}}
    class R:
        def __init__(self, body): self.body = body
        def raise_for_status(self): pass
        def json(self): return self.body
    with patch("app.requests.get", return_value=R([loc(10), loc(20)])):
        out = appmod.get_weather_many(["Seoul", "Jeju"])
    assert [(o["city"], o["temperature"]) for o in out] == [("Seoul", 10), ("Jeju", 20)]
    with patch("app.requests.get", return_value=R(loc(5))):  # single city -> object, not list
        assert appmod.get_weather("Busan")["temperature"] == 5

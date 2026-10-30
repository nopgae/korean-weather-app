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

"""Weather client tests: fallback, retries, and not leaking the key."""

import pytest
import requests

import config
import weather


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


TOMORROW_PAYLOAD = {"data": {"values": {"temperature": 31.2, "humidity": 55}}}
OPEN_METEO_PAYLOAD = {
    "current": {"temperature_2m": 24.5, "relative_humidity_2m": 70},
    "daily": {
        "precipitation_probability_max": [40],
        "et0_fao_evapotranspiration": [4.1],
    },
}


@pytest.fixture(autouse=True)
def _online(monkeypatch):
    """Network is mocked here, so turn offline mode off."""
    monkeypatch.setattr(config, "OFFLINE_MODE", False)
    monkeypatch.setattr(config, "ALLOW_KEYLESS_FALLBACKS", True)
    monkeypatch.setattr(weather.time, "sleep", lambda seconds: None)


def _sequence(*outcomes):
    """A fake requests.get that returns/raises each outcome in turn."""
    calls = []

    def _get(url, *args, **kwargs):
        outcome = outcomes[len(calls)]
        calls.append(url)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    _get.calls = calls
    return _get


def _route(tomorrow=None, open_meteo=None):
    """Build a fake requests.get that answers per host."""

    def _get(url, *args, **kwargs):
        handler = tomorrow if "tomorrow.io" in url else open_meteo
        if handler is None:
            raise AssertionError(f"Unexpected request to {url}")
        if isinstance(handler, Exception):
            raise handler
        return _FakeResponse(handler)

    return _get


def test_uses_tomorrow_io_when_configured(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "test-key")
    monkeypatch.setattr(weather.requests, "get", _route(tomorrow=TOMORROW_PAYLOAD))

    report = weather.get_weather_info(29.4, 76.9)

    assert "Tomorrow.io" in report
    assert "31.2" in report
    assert "fallback" not in report.lower()


def test_missing_key_falls_back_to_open_meteo(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "")
    monkeypatch.setattr(weather.requests, "get", _route(open_meteo=OPEN_METEO_PAYLOAD))

    report = weather.get_weather_info(29.4, 76.9)

    assert "Open-Meteo" in report
    assert "24.5" in report
    assert "fallback" in report.lower()


def test_failing_key_falls_back_to_open_meteo(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "revoked-key")
    monkeypatch.setattr(
        weather.requests,
        "get",
        _route(
            tomorrow=requests.HTTPError("401 Unauthorized"),
            open_meteo=OPEN_METEO_PAYLOAD,
        ),
    )

    report = weather.get_weather_info(29.4, 76.9)

    assert "Open-Meteo" in report


def test_no_fallback_when_disabled(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "")
    monkeypatch.setattr(config, "ALLOW_KEYLESS_FALLBACKS", False)
    monkeypatch.setattr(weather.requests, "get", _route())  # any call would fail

    report = weather.get_weather_info(29.4, 76.9)

    assert "unavailable" in report.lower()


def test_both_sources_down(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "")
    monkeypatch.setattr(
        weather.requests, "get", _route(open_meteo=requests.ConnectionError("down"))
    )

    report = weather.get_weather_info(29.4, 76.9)

    assert "unavailable" in report.lower()


def test_network_failure_does_not_expose_the_key(monkeypatch):
    monkeypatch.setattr(config, "TOMORROW_API_KEY", "super-secret-key")
    leak = requests.ConnectionError("failed connecting to ...?apikey=super-secret-key")
    monkeypatch.setattr(weather.requests, "get", _route(tomorrow=leak, open_meteo=leak))

    report = weather.get_weather_info(29.4, 76.9)

    assert "super-secret-key" not in report


class TestRetries:
    @pytest.fixture(autouse=True)
    def _keyless(self, monkeypatch):
        monkeypatch.setattr(config, "TOMORROW_API_KEY", "")

    def test_timeout_then_success_recovers(self, monkeypatch):
        fake = _sequence(requests.ReadTimeout("stalled"), _FakeResponse(OPEN_METEO_PAYLOAD))
        monkeypatch.setattr(weather.requests, "get", fake)

        conditions = weather.get_current_conditions(30.9, 75.85)

        assert conditions["source"] == "Open-Meteo"
        assert len(fake.calls) == 2

    def test_server_error_then_success_recovers(self, monkeypatch):
        fake = _sequence(_FakeResponse({}, status_code=503), _FakeResponse(OPEN_METEO_PAYLOAD))
        monkeypatch.setattr(weather.requests, "get", fake)

        assert weather.get_current_conditions(30.9, 75.85)["source"] == "Open-Meteo"
        assert len(fake.calls) == 2

    def test_client_error_is_not_retried(self, monkeypatch):
        fake = _sequence(_FakeResponse({}, status_code=401))
        monkeypatch.setattr(weather.requests, "get", fake)

        assert "error" in weather.get_current_conditions(30.9, 75.85)
        assert len(fake.calls) == 1

    def test_gives_up_after_the_retry_budget(self, monkeypatch):
        attempts = [requests.ReadTimeout("stalled")] * weather.RETRY_ATTEMPTS
        fake = _sequence(*attempts)
        monkeypatch.setattr(weather.requests, "get", fake)

        assert "error" in weather.get_current_conditions(30.9, 75.85)
        assert len(fake.calls) == weather.RETRY_ATTEMPTS

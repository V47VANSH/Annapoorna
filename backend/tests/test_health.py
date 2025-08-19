"""API tests with no external services configured."""

import pytest
from fastapi.testclient import TestClient

import config
import main


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


def test_app_imports_without_external_services():
    assert main.app is not None


def test_health_endpoint_reports_subsystems(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    for key in (
        "model_present",
        "llm_configured",
        "earth_engine_configured",
        "weather_configured",
        "database_persistent",
        "fallbacks_enabled",
        "demo_mode",
    ):
        assert key in body


def test_health_reports_in_memory_store_when_offline(client):
    assert client.get("/health").json()["database_persistent"] is False


def test_chat_answers_offline_when_llm_unconfigured(client):
    response = client.post(
        "/chat", json={"message": "How should I irrigate?", "user_id": "u1"}
    )

    assert response.status_code == 200
    assert "built-in knowledge base" in response.json()["response"]


def test_chat_returns_503_when_fallbacks_disabled(client, monkeypatch):
    monkeypatch.setattr(config, "ALLOW_KEYLESS_FALLBACKS", False)

    response = client.post("/chat", json={"message": "hello", "user_id": "u1"})

    assert response.status_code == 503


def test_register_rejects_malformed_email(client):
    response = client.post(
        "/register",
        json={
            "name": "Test",
            "address": "Somewhere",
            "email": "not-an-email",
            "phone": "123",
            "location": [1.0, 2.0, 3.0, 4.0],
        },
    )

    assert response.status_code == 422


class TestDemoFlow:
    """The demo user used by "skip registration"."""

    def test_demo_endpoint_returns_seeded_user(self, client):
        response = client.get("/demo")

        assert response.status_code == 200
        assert response.json()["id"] == config.DEMO_USER_ID

    def test_demo_profile_is_readable(self, client):
        demo_id = client.get("/demo").json()["id"]

        profile = client.get(f"/profile/{demo_id}")

        assert profile.status_code == 200
        assert profile.json()["name"] == "Demo Farmer"
        assert len(profile.json()["bounding_box"]) == 4

    def test_demo_dashboard_endpoints_respond(self, client):
        demo_id = client.get("/demo").json()["id"]

        assert client.get(f"/allReports/{demo_id}").status_code == 200
        assert client.get(f"/allChats/{demo_id}").status_code == 200
        assert client.get(f"/latestReport/{demo_id}").status_code == 200

    def test_demo_is_idempotent(self, client):
        first = client.get("/demo").json()["id"]
        second = client.get("/demo").json()["id"]
        assert first == second

    def test_demo_can_be_disabled(self, client, monkeypatch):
        monkeypatch.setattr(config, "DEMO_MODE", False)
        assert client.get("/demo").status_code == 404


def test_register_then_login_round_trip(client):
    """Register and log in using the in-memory store."""
    registered = client.post(
        "/register",
        json={
            "name": "Round Trip",
            "address": "Amritsar",
            "email": "roundtrip@example.com",
            "phone": "123",
            "location": [31.5, 31.7, 74.8, 75.0],
        },
    ).json()

    logged_in = client.post("/login", json={"email": "roundtrip@example.com"}).json()

    assert registered["id"] == logged_in["id"]

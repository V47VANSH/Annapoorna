"""Tests for the in-memory store, offline advice and Earth Engine setup errors."""

import pytest
from pymongo import DESCENDING

import chatbot
import config
import offline_advice
import predict
from memory_store import InMemoryCollection, InMemoryDatabase


class TestOfflineAdviceCoverage:
    """Every class the model can predict should have specific advice."""

    def test_every_class_maps_to_a_specific_condition(self):
        unmatched = [
            label
            for label in predict.CLASS_NAMES
            if offline_advice.identify_condition(label)
            is offline_advice.GENERIC_CONDITION
        ]
        assert unmatched == [], f"No guidance for: {unmatched}"

    def test_every_class_names_its_crop(self):
        missing = [
            label
            for label in predict.CLASS_NAMES
            if offline_advice.identify_crop(label) is None
        ]
        assert missing == [], f"No crop for: {missing}"

    def test_healthy_leaves_are_not_told_to_spray(self):
        report = offline_advice.build_disease_report("Healthy Wheat")
        assert "No treatment needed" in report

    def test_report_has_all_eight_sections(self):
        report = offline_advice.build_disease_report("Wheat___Yellow_Rust")
        for heading in range(1, 9):
            assert f"### {heading}." in report

    def test_low_confidence_is_flagged(self):
        report = offline_advice.build_disease_report("Rice Blast", confidence=0.31)
        assert "low-confidence" in report

    def test_high_confidence_is_not_flagged(self):
        report = offline_advice.build_disease_report("Rice Blast", confidence=0.93)
        assert "low-confidence" not in report

    def test_reports_are_labelled_as_offline(self):
        assert "built-in knowledge base" in offline_advice.build_disease_report(
            "Wilt"
        )


class TestChatbotFallback:
    def test_disease_advice_falls_back_without_llm(self):
        advice = chatbot.image_response("Rice Blast", "fallback-user", 0.88)
        assert "tricyclazole" in advice

    def test_chat_reply_matches_the_topic(self):
        reply = chatbot.returnResponse("when should I irrigate?", "fallback-user")
        assert "moisture" in reply.lower()

    def test_fallback_can_be_refused(self, monkeypatch):
        monkeypatch.setattr(config, "ALLOW_KEYLESS_FALLBACKS", True)
        try:
            chatbot.returnResponse("hi", "fallback-user", allow_fallback=False)
        except chatbot.LLMUnavailable:
            return
        raise AssertionError("allow_fallback=False should raise without an LLM")


class TestInMemoryStore:
    def test_insert_and_find_one(self):
        users = InMemoryCollection("users")
        inserted = users.insert_one({"email": "a@example.com"}).inserted_id

        assert users.find_one({"email": "a@example.com"})["_id"] == inserted
        assert users.find_one({"email": "missing@example.com"}) is None

    def test_update_one_sets_fields(self):
        users = InMemoryCollection("users")
        users.insert_one({"email": "a@example.com", "name": "old"})

        users.update_one({"email": "a@example.com"}, {"$set": {"name": "new"}})

        assert users.find_one({"email": "a@example.com"})["name"] == "new"

    def test_find_one_honours_sort(self):
        reports = InMemoryCollection("reports")
        for day in (1, 3, 2):
            reports.insert_one({"user_id": "u", "date": day})

        latest = reports.find_one({"user_id": "u"}, sort=[("date", DESCENDING)])

        assert latest["date"] == 3

    def test_cursor_sort_descending(self):
        reports = InMemoryCollection("reports")
        for day in (1, 3, 2):
            reports.insert_one({"user_id": "u", "date": day})

        dates = [r["date"] for r in reports.find({"user_id": "u"}).sort("date", -1)]

        assert dates == [3, 2, 1]

    def test_returned_documents_are_copies(self):
        users = InMemoryCollection("users")
        users.insert_one({"email": "a@example.com", "name": "original"})

        users.find_one({"email": "a@example.com"})["name"] = "mutated"

        assert users.find_one({"email": "a@example.com"})["name"] == "original"

    def test_database_reuses_collections(self):
        db = InMemoryDatabase()
        assert db["Profiles"] is db["Profiles"]


class TestEarthEngineSetup:
    """Bad config should give a clear error message."""

    @pytest.fixture(autouse=True)
    def _online(self, monkeypatch):
        import sattelite_report

        monkeypatch.setattr(config, "OFFLINE_MODE", False)
        monkeypatch.setattr(sattelite_report, "_ee_initialized", False)

    def test_missing_project_id_explains_the_fix(self, monkeypatch):
        import sattelite_report

        monkeypatch.setattr(config, "GEE_PROJECT_ID", "")

        with pytest.raises(sattelite_report.EarthEngineUnavailable, match="PROJECT_ID"):
            sattelite_report.ensure_earth_engine()

    def test_bad_service_account_key_names_the_setting(self, monkeypatch, tmp_path):
        import sattelite_report

        monkeypatch.setattr(config, "GEE_PROJECT_ID", "some-project")
        monkeypatch.setattr(
            config, "GEE_SERVICE_ACCOUNT_KEY", str(tmp_path / "missing-key.json")
        )

        with pytest.raises(
            sattelite_report.EarthEngineUnavailable, match="GEE_SERVICE_ACCOUNT_KEY"
        ):
            sattelite_report.ensure_earth_engine()

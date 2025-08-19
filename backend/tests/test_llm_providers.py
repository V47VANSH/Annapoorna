"""Tests for choosing and building the chat model (no network calls)."""

import pytest
from langchain_core.messages import AIMessage

import chatbot
import config


@pytest.fixture(autouse=True)
def _clean_llm_config(monkeypatch):
    """Online, with no provider configured."""
    monkeypatch.setattr(config, "OFFLINE_MODE", False)
    monkeypatch.setattr(config, "ALLOW_KEYLESS_FALLBACKS", True)
    for name in (
        "LLM_PROVIDER",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_THINKING_BUDGET",
        "OLLAMA_MODEL",
        "LLM_BASE_URL",
    ):
        monkeypatch.setattr(config, name, "")
    monkeypatch.setattr(chatbot, "_llm", None)
    monkeypatch.setattr(chatbot, "_llm_signature", None)


def _use_gemini(monkeypatch, model="gemini-test-model"):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(config, "GEMINI_MODEL", model)


class TestProviderResolution:
    def test_nothing_configured_means_no_provider(self):
        assert chatbot.resolve_provider() == ""
        assert chatbot.is_available() is False

    def test_gemini_key_selects_gemini(self, monkeypatch):
        _use_gemini(monkeypatch)
        assert chatbot.resolve_provider() == "gemini"

    def test_gemini_wins_over_other_providers(self, monkeypatch):
        _use_gemini(monkeypatch)
        monkeypatch.setattr(config, "LLM_BASE_URL", "http://localhost:8001/v1")
        monkeypatch.setattr(config, "OLLAMA_MODEL", "llama3.2")
        assert chatbot.resolve_provider() == "gemini"

    def test_ollama_model_selects_ollama(self, monkeypatch):
        monkeypatch.setattr(config, "OLLAMA_MODEL", "llama3.2")
        assert chatbot.resolve_provider() == "ollama"

    def test_explicit_provider_overrides_auto_detection(self, monkeypatch):
        _use_gemini(monkeypatch)
        monkeypatch.setattr(config, "OLLAMA_MODEL", "llama3.2")
        monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
        assert chatbot.resolve_provider() == "ollama"


class TestModelConstruction:
    def test_builds_gemini_from_env(self, monkeypatch):
        from langchain_google_genai import ChatGoogleGenerativeAI

        _use_gemini(monkeypatch, model="gemini-from-env")

        llm = chatbot._get_llm()

        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model.endswith("gemini-from-env")
        assert llm.google_api_key.get_secret_value() == "test-gemini-key"

    def test_gemini_thinking_budget_is_passed_through(self, monkeypatch):
        _use_gemini(monkeypatch)
        monkeypatch.setattr(config, "GEMINI_THINKING_BUDGET", "0")

        assert chatbot._get_llm().thinking_budget == 0

    def test_builds_ollama_from_env(self, monkeypatch):
        from langchain_ollama import ChatOllama

        monkeypatch.setattr(config, "OLLAMA_MODEL", "llama3.2")
        monkeypatch.setattr(config, "OLLAMA_BASE_URL", "http://ollama:11434")

        llm = chatbot._get_llm()

        assert isinstance(llm, ChatOllama)
        assert llm.model == "llama3.2"
        assert llm.base_url == "http://ollama:11434"

    def test_builds_openai_compatible_from_env(self, monkeypatch):
        from langchain_openai import ChatOpenAI

        monkeypatch.setattr(config, "LLM_BASE_URL", "http://localhost:8001/v1")
        monkeypatch.setattr(config, "LLM_MODEL", "some-model")

        llm = chatbot._get_llm()

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "some-model"

    def test_model_is_rebuilt_when_settings_change(self, monkeypatch):
        _use_gemini(monkeypatch, model="first-model")
        first = chatbot._get_llm()

        monkeypatch.setattr(config, "GEMINI_MODEL", "second-model")
        second = chatbot._get_llm()

        assert first is not second
        assert second.model.endswith("second-model")

    def test_model_is_cached_when_settings_are_unchanged(self, monkeypatch):
        _use_gemini(monkeypatch)
        assert chatbot._get_llm() is chatbot._get_llm()


class TestMisconfiguration:
    def test_gemini_key_without_model_names_the_missing_setting(self, monkeypatch):
        monkeypatch.setattr(config, "GEMINI_API_KEY", "test-gemini-key")

        with pytest.raises(chatbot.LLMUnavailable, match="GEMINI_MODEL"):
            chatbot._get_llm()

    def test_unknown_provider_is_rejected(self, monkeypatch):
        monkeypatch.setattr(config, "LLM_PROVIDER", "not-a-provider")

        with pytest.raises(chatbot.LLMUnavailable, match="Unknown LLM_PROVIDER"):
            chatbot._get_llm()

    def test_misconfiguration_falls_back_instead_of_failing(self, monkeypatch):
        monkeypatch.setattr(config, "GEMINI_API_KEY", "test-gemini-key")

        reply = chatbot.returnResponse("how do I irrigate?", "misconfigured")

        assert "built-in knowledge base" in reply

    def test_describe_never_exposes_the_key(self, monkeypatch):
        _use_gemini(monkeypatch)

        info = chatbot.describe()

        assert info == {"provider": "gemini", "model": "gemini-test-model", "configured": True}
        assert "test-gemini-key" not in str(info)


class _FakeModel:
    """Fake chat model that returns fixed content."""

    def __init__(self, content):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return AIMessage(content=self.content)


class TestReplyHandling:
    def test_gemini_style_block_content_is_flattened(self, monkeypatch):
        fake = _FakeModel([{"type": "text", "text": "Water "}, {"type": "text", "text": "weekly."}])
        monkeypatch.setattr(chatbot, "_get_llm", lambda: fake)

        assert chatbot.returnResponse("irrigation?", "blocks") == "Water weekly."

    def test_empty_reply_falls_back(self, monkeypatch):
        monkeypatch.setattr(chatbot, "_get_llm", lambda: _FakeModel(""))

        reply = chatbot.returnResponse("how do I irrigate?", "empty")

        assert "built-in knowledge base" in reply

    def test_history_is_sent_with_each_turn(self, monkeypatch):
        fake = _FakeModel("Noted.")
        monkeypatch.setattr(chatbot, "_get_llm", lambda: fake)
        chatbot.resetConversation("history")

        chatbot.returnResponse("first question", "history")
        chatbot.returnResponse("second question", "history")

        assert [m.content for m in fake.calls[1]] == [
            "first question",
            "Noted.",
            "second question",
        ]

    def test_disease_advice_uses_the_model_when_configured(self, monkeypatch):
        _use_gemini(monkeypatch)
        fake = _FakeModel("Model-written advice.")
        monkeypatch.setattr(chatbot, "_get_llm", lambda: fake)

        advice = chatbot.image_response("Rice Blast", "advice", 0.9)

        assert advice == "Model-written advice."
        assert "Rice Blast" in fake.calls[0][-1].content

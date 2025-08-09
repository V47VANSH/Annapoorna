"""Chat with the farmer using Gemini, Ollama or an OpenAI-compatible model.

History is stored per user id so different users don't share a conversation.
"""

import logging
import threading

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

import config
import offline_advice

logger = logging.getLogger(__name__)

DEFAULT_SESSION = "__default__"

# Keep history small enough to fit in the model's context window.
MAX_HISTORY_MESSAGES = 40

SYSTEM_PROMPT_TEMPLATE = (
    "You are a highly knowledgeable and helpful expert in plant pathology and crop health. "
    "Your job is to analyze and advise farmers about their crops based on the following report. "
    "Be clear, helpful, and specific.\n\n"
    "It is advised to explain problem in an easy way as the farmer you are answering to might be "
    "a little uneducated. Be more solution oriented, avoid tricky terms."
    "\n\nReport:\n{report}"
)

DISEASE_PROMPT_TEMPLATE = """
You are an expert plant pathologist. A farmer has uploaded an image of a crop leaf, and it has been identified as suffering from the following disease: **{disease_name}**.

Please provide a detailed and structured report including the following:

1. **Disease Name**
2. **Description of the Disease**
3. **Common Causes**
4. **Affected Crops**
5. **Symptoms**
6. **Prevention Methods**
7. **Recommended Treatments or Solutions**
8. **Environmental Conditions that Promote this Disease**

Make the output concise but informative, use markdown formatting with headings or bullet points where appropriate.
"""


class LLMUnavailable(RuntimeError):
    """The chat model isn't configured or can't be reached."""


PROVIDERS = ("gemini", "ollama", "openai")

_llm: BaseChatModel | None = None
_llm_signature: tuple | None = None
_histories: dict[str, list[BaseMessage]] = {}
_lock = threading.Lock()


def resolve_provider() -> str:
    """LLM_PROVIDER if set, otherwise the first configured provider, or ""."""
    if config.LLM_PROVIDER:
        return config.LLM_PROVIDER
    if config.GEMINI_API_KEY:
        return "gemini"
    if config.LLM_BASE_URL:
        return "openai"
    if config.OLLAMA_MODEL:
        return "ollama"
    return ""


def _model_name(provider: str) -> str:
    return {
        "gemini": config.GEMINI_MODEL,
        "ollama": config.OLLAMA_MODEL,
        "openai": config.LLM_MODEL,
    }.get(provider, "")


def _missing_settings(provider: str) -> list[str]:
    """Env vars the provider needs that aren't set."""
    required = {
        "gemini": {
            "GEMINI_API_KEY": config.GEMINI_API_KEY,
            "GEMINI_MODEL": config.GEMINI_MODEL,
        },
        "ollama": {"OLLAMA_MODEL": config.OLLAMA_MODEL},
        "openai": {"LLM_BASE_URL": config.LLM_BASE_URL, "LLM_MODEL": config.LLM_MODEL},
    }[provider]
    return [name for name, value in required.items() if not value]


def describe() -> dict[str, str | bool | None]:
    """Provider and model for /health (no keys)."""
    provider = resolve_provider()
    valid = provider in PROVIDERS
    return {
        "provider": provider or None,
        "model": _model_name(provider) or None if valid else None,
        "configured": is_available(),
    }


def _build_llm(provider: str) -> BaseChatModel:
    # imported here so unused provider SDKs aren't loaded
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        options = {}
        if config.GEMINI_THINKING_BUDGET:
            options["thinking_budget"] = int(config.GEMINI_THINKING_BUDGET)

        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=config.LLM_TEMPERATURE,
            max_output_tokens=config.LLM_MAX_TOKENS,
            timeout=config.LLM_TIMEOUT_SECONDS,
            max_retries=2,
            **options,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            num_predict=config.LLM_MAX_TOKENS,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        timeout=config.LLM_TIMEOUT_SECONDS,
        max_retries=2,
    )


def _get_llm() -> BaseChatModel:
    """Build the chat model on first use. Rebuilt if the settings change."""
    global _llm, _llm_signature

    if config.OFFLINE_MODE:
        raise LLMUnavailable("OFFLINE_MODE is enabled; the LLM is disabled.")

    provider = resolve_provider()
    if not provider:
        raise LLMUnavailable(
            "No chat model is configured. Set GEMINI_API_KEY and GEMINI_MODEL, "
            "or OLLAMA_MODEL, or LLM_BASE_URL in backend/.env."
        )
    if provider not in PROVIDERS:
        raise LLMUnavailable(
            f"Unknown LLM_PROVIDER '{provider}'. Use one of: {', '.join(PROVIDERS)}."
        )

    missing = _missing_settings(provider)
    if missing:
        raise LLMUnavailable(
            f"LLM_PROVIDER is '{provider}' but {', '.join(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} not set in backend/.env."
        )

    # includes the keys so a changed key takes effect
    signature = (
        provider,
        _model_name(provider),
        config.GEMINI_API_KEY,
        config.OLLAMA_BASE_URL,
        config.LLM_BASE_URL,
        config.LLM_API_KEY,
        config.GEMINI_THINKING_BUDGET,
    )

    with _lock:
        if _llm is None or _llm_signature != signature:
            try:
                _llm = _build_llm(provider)
            except Exception as exc:
                raise LLMUnavailable(
                    f"Could not initialise the {provider} chat model: {exc}"
                ) from exc
            _llm_signature = signature
            logger.info("Chat model ready: %s / %s", provider, _model_name(provider))
        return _llm


def _trim(history: list[BaseMessage]) -> list[BaseMessage]:
    """Drop the oldest messages but keep the system prompt."""
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history

    system = [m for m in history[:1] if isinstance(m, SystemMessage)]
    return system + history[-(MAX_HISTORY_MESSAGES - len(system)) :]


def _strip_reasoning(text: str) -> str:
    """Remove the <think> block some models (e.g. DeepSeek-R1) add."""
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text.strip()


def _reply_text(reply: BaseMessage) -> str:
    """Reply text. Gemini returns a list of content blocks, .text joins them."""
    text = reply.text
    if callable(text):  # older langchain-core
        text = text()
    return _strip_reasoning(text or "")


def is_available() -> bool:
    """True if a chat model is configured."""
    if config.OFFLINE_MODE:
        return False
    provider = resolve_provider()
    return provider in PROVIDERS and not _missing_settings(provider)


def returnResponse(
    user_input: str,
    session_id: str = DEFAULT_SESSION,
    allow_fallback: bool = True,
) -> str:
    """Send a message and return the reply.

    If the LLM isn't available this answers from offline_advice instead,
    unless allow_fallback is False.
    """
    try:
        llm = _get_llm()
    except LLMUnavailable:
        if allow_fallback and config.ALLOW_KEYLESS_FALLBACKS:
            with _lock:
                has_context = bool(_histories.get(session_id))
            return offline_advice.answer_question(user_input, has_context)
        raise

    with _lock:
        history = list(_histories.get(session_id, []))

    history.append(HumanMessage(content=user_input))

    try:
        reply = llm.invoke(_trim(history))
    except Exception as exc:
        logger.warning("LLM request failed: %s", exc)
        if allow_fallback and config.ALLOW_KEYLESS_FALLBACKS:
            return offline_advice.answer_question(user_input, len(history) > 1)
        raise LLMUnavailable(f"The language model could not be reached: {exc}") from exc

    text = _reply_text(reply)
    if not text:
        # happens when a Gemini thinking model uses up the token budget
        logger.warning(
            "The chat model returned an empty reply; raise LLM_MAX_TOKENS or set "
            "GEMINI_THINKING_BUDGET=0."
        )
        if allow_fallback and config.ALLOW_KEYLESS_FALLBACKS:
            return offline_advice.answer_question(user_input, len(history) > 1)
        raise LLMUnavailable("The language model returned an empty reply.")

    history.append(AIMessage(content=text))
    with _lock:
        _histories[session_id] = _trim(history)

    return text


def resetConversation(session_id: str = DEFAULT_SESSION) -> None:
    """Clear a session's history."""
    with _lock:
        _histories.pop(session_id, None)
    logger.info("Cleared conversation memory for session %s", session_id)


def image_response(
    disease_name: str,
    session_id: str = DEFAULT_SESSION,
    confidence: float | None = None,
) -> str:
    """Treatment advice for a predicted disease (offline advice if no LLM)."""
    if not is_available() and config.ALLOW_KEYLESS_FALLBACKS:
        return offline_advice.build_disease_report(disease_name, confidence)

    try:
        return returnResponse(
            DISEASE_PROMPT_TEMPLATE.format(disease_name=disease_name),
            session_id=session_id,
            allow_fallback=False,
        )
    except LLMUnavailable:
        if config.ALLOW_KEYLESS_FALLBACKS:
            return offline_advice.build_disease_report(disease_name, confidence)
        raise


def addContext(report: str, session_id: str = DEFAULT_SESSION) -> None:
    """Start a new conversation with the latest field report as context."""
    with _lock:
        _histories[session_id] = [
            SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(report=report))
        ]
    logger.info("Seeded conversation context for session %s", session_id)

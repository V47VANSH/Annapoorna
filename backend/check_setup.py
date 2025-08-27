"""Check that each external service actually works with the keys in .env.

    cd backend
    uv run python check_setup.py

Makes one real request per service. Exits with 1 if a configured service
fails; services that aren't configured are only warnings.
"""

from __future__ import annotations

import shutil
import sys
import time

import config

OK, WARN, FAIL = "[ OK ]", "[WARN]", "[FAIL]"
_failures = 0


def report(status: str, name: str, detail: str) -> None:
    global _failures
    if status == FAIL:
        _failures += 1
    print(f"{status} {name:<18} {detail}")


def check_mongodb() -> None:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    try:
        MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=2000).admin.command("ping")
        report(OK, "MongoDB", f"connected, database '{config.MONGODB_DB_NAME}'")
    except PyMongoError as exc:
        report(
            WARN,
            "MongoDB",
            f"unreachable ({exc.__class__.__name__}); the app will use the "
            "in-memory store and lose data on restart",
        )


def check_disease_model() -> None:
    import predict

    if not config.MODEL_PATH.exists():
        report(FAIL, "Disease model", f"weights missing at {config.MODEL_PATH}; run 'git lfs pull'")
        return
    if config.MODEL_PATH.stat().st_size < 1_000_000:
        report(
            FAIL,
            "Disease model",
            "weights file is a Git LFS pointer, not the model; run 'git lfs pull'",
        )
        return

    started = time.monotonic()
    try:
        model = predict._get_model()
    except Exception as exc:
        report(FAIL, "Disease model", f"failed to load: {exc}")
        return
    outputs = model.output_shape[-1]
    if outputs != len(predict.CLASS_NAMES):
        report(
            FAIL,
            "Disease model",
            f"{outputs} output units but {len(predict.CLASS_NAMES)} class names",
        )
        return
    report(OK, "Disease model", f"{outputs} classes, loaded in {time.monotonic() - started:.0f}s")


def check_chat_model() -> None:
    import chatbot

    provider = chatbot.resolve_provider()
    if not provider:
        report(
            WARN,
            "Chat model",
            "not configured; chat uses the built-in knowledge base "
            "(set GEMINI_API_KEY + GEMINI_MODEL)",
        )
        return

    label = f"{provider} / {chatbot._model_name(provider) or '?'}"
    try:
        llm = chatbot._get_llm()
        reply = llm.invoke("Reply with the single word: OK")
        text = chatbot._reply_text(reply)
    except Exception as exc:
        report(FAIL, "Chat model", f"{label}: {exc}")
        return

    if not text:
        report(
            FAIL,
            "Chat model",
            f"{label}: empty reply; raise LLM_MAX_TOKENS or set GEMINI_THINKING_BUDGET=0",
        )
        return
    report(OK, "Chat model", f"{label} replied: {text[:40]!r}")


def check_earth_engine() -> None:
    import sattelite_report

    if not config.GEE_PROJECT_ID:
        report(
            WARN,
            "Earth Engine",
            "PROJECT_ID not set; reports will contain weather only "
            "(see README)",
        )
        return

    try:
        sattelite_report.ensure_earth_engine()
        import ee

        # small query to make sure the credentials really work
        count = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(ee.Geometry.Point([75.85, 30.90]))
            .filterDate("2025-01-01", "2025-02-01")
            .size()
            .getInfo()
        )
    except Exception as exc:
        report(FAIL, "Earth Engine", str(exc))
        return

    method = "service account" if config.GEE_SERVICE_ACCOUNT_KEY else "user login"
    report(
        OK,
        "Earth Engine",
        f"project '{config.GEE_PROJECT_ID}' via {method}; "
        f"test query found {count} Sentinel-2 scenes",
    )


def check_weather() -> None:
    import weather

    conditions = weather.get_current_conditions(30.90, 75.85)
    if "error" in conditions:
        report(FAIL, "Weather", conditions["error"])
        return

    note = " (keyless fallback)" if "fallback_reason" in conditions else ""
    report(
        OK,
        "Weather",
        f"{conditions['source']}{note}: {conditions['temperature']}°C at the demo farm",
    )


def check_voice() -> None:
    if shutil.which("ffmpeg") is None:
        report(
            WARN,
            "Voice input",
            "ffmpeg not on PATH; Whisper cannot decode audio (https://ffmpeg.org/download.html)",
        )
        return
    report(
        OK,
        "Voice input",
        f"ffmpeg found; Whisper '{config.WHISPER_MODEL_SIZE}' downloads on first use",
    )


def main() -> int:
    if config.OFFLINE_MODE:
        print("OFFLINE_MODE=true disables every external service; set it to false first.")
        return 1

    print("Checking Annapoorna's external services with real requests...\n")
    for check in (
        check_mongodb,
        check_chat_model,
        check_earth_engine,
        check_weather,
        check_voice,
        check_disease_model,
    ):
        try:
            check()
        except Exception as exc:
            report(FAIL, check.__name__.removeprefix("check_"), f"unexpected error: {exc}")

    print()
    if _failures:
        print(f"{_failures} check(s) failed. Fix the messages above, then rerun.")
        return 1
    print("All configured services work. Restart the backend to pick up any .env changes.")
    return 0


if __name__ == "__main__":
    import logging
    import os

    # quiet tensorflow logs
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    logging.basicConfig(level=logging.ERROR)
    # avoid encoding errors when output is redirected on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())

"""Speech to text for voice input (English and Indian languages)."""

import logging
import os
import tempfile
import threading

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse

import config

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "bn": "Bengali",
    "mr": "Marathi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "auto": "Auto-detect (Indian languages + English)",
}

INDIAN_LANGUAGE_CODES = ["hi", "pa", "ta", "te", "gu", "bn", "mr", "kn", "ml", "en"]

FALLBACK_LANGUAGE = "hi"
MIN_DETECTION_CONFIDENCE = 0.1

_model = None
_lock = threading.Lock()


class TranscriptionUnavailable(RuntimeError):
    """Raised when the Whisper model cannot be loaded."""


def _get_model():
    """Load Whisper on first use (the first load downloads the model)."""
    global _model
    if _model is not None:
        return _model

    if config.OFFLINE_MODE:
        raise TranscriptionUnavailable(
            "OFFLINE_MODE is enabled; transcription is disabled."
        )

    with _lock:
        if _model is None:
            import whisper

            logger.info("Loading Whisper model '%s'", config.WHISPER_MODEL_SIZE)
            _model = whisper.load_model(config.WHISPER_MODEL_SIZE)
    return _model


def _detect_language(model, audio_path: str) -> str:
    """Detect the spoken language, constrained to the supported set."""
    import whisper

    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    _, probs = model.detect_language(mel)

    supported = {
        lang: prob for lang, prob in probs.items() if lang in INDIAN_LANGUAGE_CODES
    }
    if not supported:
        return FALLBACK_LANGUAGE

    detected = max(supported, key=supported.get)
    if supported[detected] < MIN_DETECTION_CONFIDENCE:
        return FALLBACK_LANGUAGE
    return detected


# both paths, the redirect from /transcribe to /transcribe/ can lose the
# upload body in some browsers
@router.post("/transcribe")
@router.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(
        "auto", description="Language code, e.g. en, hi, or auto"
    ),
):
    if language not in SUPPORTED_LANGUAGES:
        return JSONResponse(
            content={
                "error": f"Unsupported language. Supported: {list(SUPPORTED_LANGUAGES)}"
            },
            status_code=400,
        )

    try:
        model = _get_model()
    except TranscriptionUnavailable as exc:
        return JSONResponse(content={"error": str(exc)}, status_code=503)
    except Exception as exc:
        logger.exception("Whisper model failed to load")
        return JSONResponse(
            content={"error": f"Transcription model unavailable: {exc}"},
            status_code=503,
        )

    # don't use the uploaded filename on disk (path traversal)
    suffix = os.path.splitext(file.filename or "")[1][:10] or ".wav"
    temp_path = None
    try:
        contents = await file.read()
        if len(contents) > config.MAX_UPLOAD_BYTES:
            return JSONResponse(
                content={"error": "Audio file is too large."}, status_code=413
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(contents)
            temp_path = handle.name

        transcribe_options = {"fp16": False, "task": "transcribe"}
        transcribe_options["language"] = (
            _detect_language(model, temp_path) if language == "auto" else language
        )

        result = model.transcribe(temp_path, **transcribe_options)

        detected = result.get("language", transcribe_options["language"])
        if detected not in INDIAN_LANGUAGE_CODES:
            transcribe_options["language"] = FALLBACK_LANGUAGE
            result = model.transcribe(temp_path, **transcribe_options)
            detected = FALLBACK_LANGUAGE

        return JSONResponse(
            content={
                "transcription": result["text"],
                "detected_language": detected,
                "language_name": SUPPORTED_LANGUAGES.get(detected, detected),
            },
            status_code=200,
        )

    except Exception as exc:
        logger.exception("Transcription failed")
        return JSONResponse(content={"error": str(exc)}, status_code=500)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

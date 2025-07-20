from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse , FileResponse
import whisper
import os
from datetime import datetime
import shutil
from typing import Optional

router = APIRouter()
model = whisper.load_model("medium")

# Supported languages - restricted to Indian languages and English
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
    "auto": "Auto-detect (Indian languages + English)"
}

INDIAN_LANGUAGE_CODES = ["hi", "pa", "ta", "te", "gu", "bn", "mr", "kn", "ml", "en"]



@router.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Query("auto", description="Language code: en, hi, or auto")
):
    try:
        # Validate language parameter
        if language not in SUPPORTED_LANGUAGES:
            return JSONResponse(
                content={"error": f"Unsupported language. Supported: {list(SUPPORTED_LANGUAGES.keys())}"},
                status_code=400
            )

        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Configure transcription parameters
        transcribe_options = {
            "fp16": False,  # Better compatibility
            "task": "transcribe"
        }
        
        # Handle language detection and restriction
        if language == "auto":
            # First detect language
            audio = whisper.load_audio(temp_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            _, probs = model.detect_language(mel)
            
            # Filter probabilities to only include supported languages
            filtered_probs = {lang: prob for lang, prob in probs.items() if lang in INDIAN_LANGUAGE_CODES}
            
            if filtered_probs:
                detected_lang = max(filtered_probs, key=filtered_probs.get)
                # Additional check: if confidence is too low, default to Hindi
                if filtered_probs[detected_lang] < 0.1:
                    detected_lang = "hi"
            else:
                detected_lang = "hi"  # Default to Hindi if no supported language detected
            
            transcribe_options["language"] = detected_lang
        else:
            # Force the specified language
            transcribe_options["language"] = language

        # Perform transcription with language restriction
        result = model.transcribe(temp_path, **transcribe_options)
        
        # Double-check the detected language and override if necessary
        actual_detected_lang = result.get("language", transcribe_options["language"])
        if actual_detected_lang not in INDIAN_LANGUAGE_CODES:
            # Re-transcribe with forced Hindi if unsupported language detected
            transcribe_options["language"] = "hi"
            result = model.transcribe(temp_path, **transcribe_options)
            actual_detected_lang = "hi"
        
        transcription = result["text"]
        detected_language = actual_detected_lang

        os.remove(temp_path)

        return JSONResponse(
            content={
                "transcription": transcription,
                "detected_language": detected_language,
                "language_name": SUPPORTED_LANGUAGES.get(detected_language, detected_language)
            },
            status_code=200
        )

    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return JSONResponse(content={"error": str(e)}, status_code=500)


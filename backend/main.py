"""Annapoorna API: crop disease detection, field reports and farmer chat."""

import logging
import threading
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

import config
from chatbot import (
    LLMUnavailable,
    addContext,
    image_response,
    resetConversation,
    returnResponse,
)
from chatbot import (
    describe as describe_llm,
)
from database import (
    IS_PERSISTENT,
    ensure_indexes,
    get_all_reports,
    get_chat_by_id,
    get_chats_by_user_id,
    get_email_by_id,
    get_latest_report_by_user_id,
    get_profile_by_id,
    get_user_id_and_bounding_box,
    login,
    register,
    saveReport,
    saveTheChat,
    seed_demo_user,
)
from generateReport import generateReport
from predict import ModelUnavailable, predict_disease_with_confidence
from whisper_transcribe import router as whisper_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# email -> scheduled report job id. In memory only, so jobs are lost on restart.
user_jobs: dict[str, str] = {}

_demo_reports_started: set[str] = set()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler.start()
    try:
        ensure_indexes()
    except Exception as exc:
        logger.warning("Could not create MongoDB indexes: %s", exc)

    try:
        demo_id = seed_demo_user()
        if demo_id:
            logger.info("Demo farmer available at /dashboard/%s/home", demo_id)
    except Exception as exc:
        logger.warning("Could not seed the demo user: %s", exc)

    if not IS_PERSISTENT:
        logger.warning(
            "Running on the in-memory store: data will be lost on restart. "
            "Start MongoDB and restart to persist."
        )
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Annapoorna API",
    description="AI assistant for crop disease detection and field health reporting.",
    version="1.0.0",
    lifespan=lifespan,
)

# browsers reject "*" together with allow_credentials, so list the origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserModel(BaseModel):
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=1)
    location: list


class LoginModel(BaseModel):
    email: EmailStr


class LogoutModel(BaseModel):
    id: str


class ChatModel(BaseModel):
    user_id: str
    messages: list
    context: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str | None = None


class ChatContext(BaseModel):
    context: str
    user_id: str | None = None


def _session(user_id: str | None) -> str:
    """Conversation memory is keyed per user so sessions cannot cross-talk."""
    from chatbot import DEFAULT_SESSION

    return user_id or DEFAULT_SESSION


def periodic_task(email: str) -> None:
    """Generate and store the daily satellite + weather report for one user."""
    logger.info("Starting report generation for %s", email)
    user_data = get_user_id_and_bounding_box(email)
    if not user_data:
        logger.warning("Skipping report generation: no user for email %s", email)
        return

    try:
        report = generateReport(user_data["bounding_box"], user_data["id"])
        saveReport(user_data["id"], report)
    except Exception as exc:
        logger.exception("Report generation failed for %s: %s", email, exc)
        return

    logger.info("Report generated for %s at %s", email, datetime.now(UTC))


@app.get("/health")
def health():
    """Health check, plus which services are configured."""
    llm = describe_llm()
    return {
        "status": "ok",
        "model_present": config.MODEL_PATH.exists(),
        "llm_configured": llm["configured"],
        "llm_provider": llm["provider"],
        "llm_model": llm["model"],
        "earth_engine_configured": bool(config.GEE_PROJECT_ID),
        "weather_configured": bool(config.TOMORROW_API_KEY),
        "database_persistent": IS_PERSISTENT,
        "fallbacks_enabled": config.ALLOW_KEYLESS_FALLBACKS,
        "demo_mode": config.DEMO_MODE,
    }


@app.get("/demo")
def demo_user():
    """Id of the demo farmer, used by the "skip registration" button."""
    if not config.DEMO_MODE:
        raise HTTPException(status_code=404, detail="Demo mode is disabled.")

    demo_id = seed_demo_user()
    if not demo_id:
        raise HTTPException(status_code=503, detail="Demo user is unavailable.")

    # reports are normally made on /login, which the demo skips
    if get_latest_report_by_user_id(demo_id) is None:
        demo_email = get_email_by_id(demo_id)
        if demo_email and demo_email not in _demo_reports_started:
            _demo_reports_started.add(demo_email)
            threading.Thread(
                target=periodic_task, args=(demo_email,), daemon=True
            ).start()

    return {
        "id": demo_id,
        "name": "Demo Farmer",
        "persistent": IS_PERSISTENT,
    }


@app.post("/register")
def register_user(user: UserModel):
    return register(user)


@app.post("/login")
def login_user(data: LoginModel):
    result = login(data.model_dump())
    if "error" in result:
        return result

    email = data.email
    if email not in user_jobs:
        job_id = str(uuid4())
        scheduler.add_job(
            periodic_task,
            "cron",
            hour=config.REPORT_CRON_HOUR,
            minute=config.REPORT_CRON_MINUTE,
            args=[email],
            id=job_id,
            replace_existing=True,
        )
        user_jobs[email] = job_id
        logger.info("Scheduled daily report job %s for %s", job_id, email)

        # first report right away instead of waiting for the cron job
        threading.Thread(target=periodic_task, args=(email,), daemon=True).start()

    return result


@app.post("/logout")
def logout_user(data: LogoutModel):
    email = get_email_by_id(data.id)
    if not email:
        raise HTTPException(status_code=404, detail="User not found.")

    job_id = user_jobs.get(email)
    if not job_id:
        raise HTTPException(status_code=404, detail="No active task found for user.")

    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        logger.info("Job %s was already removed", job_id)

    user_jobs.pop(email, None)
    return {"message": f"Logged out {email}, task cancelled."}


@app.post("/chat")
def chat(request: ChatRequest):
    """Send a message to the assistant."""
    try:
        return {"response": returnResponse(request.message, _session(request.user_id))}
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/chat/{input}")
def chat_with_input(input: str, user_id: str | None = None):
    """Legacy path-parameter form, kept so older clients keep working."""
    try:
        return {"response": returnResponse(input, _session(user_id))}
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/reset")
def reset_chat(chat: ChatModel):
    """Save the current chat and start a new one with the latest report."""
    saveTheChat(chat)
    session = _session(chat.user_id)
    resetConversation(session)

    report = get_latest_report_by_user_id(chat.user_id)
    try:
        addContext(report["report"] if report else "", session)
    except LLMUnavailable as exc:
        logger.warning("Could not seed conversation context: %s", exc)

    return {"message": "Conversation reset successfully"}


@app.post("/predict")
async def predict(file: UploadFile = File(...), user_id: str | None = None):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    img_bytes = await file.read()
    if len(img_bytes) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large.")

    try:
        disease, confidence = predict_disease_with_confidence(img_bytes)
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        return JSONResponse(status_code=500, content={"error": str(exc)})

    try:
        advice = image_response(disease, _session(user_id), confidence)
    except Exception as exc:
        logger.warning("Could not generate treatment advice: %s", exc)
        advice = (
            f"**{disease}** detected (confidence {confidence:.0%}). "
            "Treatment advice is unavailable right now."
        )

    return {"disease": disease, "confidence": confidence, "response": advice}


@app.get("/allReports/{id}")
def get_all(id: str):
    return {"reports": get_all_reports(id)}


@app.get("/latestReport/{user_id}")
def get_latest(user_id: str):
    return get_latest_report_by_user_id(user_id)


@app.get("/allChats/{id}")
def all_chats(id: str):
    return get_chats_by_user_id(id)


@app.get("/profile/{user_id}")
def get_user_profile(user_id: str):
    user = get_profile_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user.get("name"),
        "address": user.get("address"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "bounding_box": user.get("bounding_box"),
    }


@app.get("/chatById/{chat_id}")
def get_chat_by_id_route(chat_id: str):
    chat = get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@app.post("/setContext")
def set_context(data: ChatContext):
    try:
        addContext(data.context, _session(data.user_id))
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"response": f"Processed context with length {len(data.context)}"}


app.include_router(whisper_router)

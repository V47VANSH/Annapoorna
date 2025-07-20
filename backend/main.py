from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from typing import Dict
from uuid import uuid4
from datetime import datetime
from chatbot import returnResponse, resetConversation, image_response
from database import register, login, saveTheChat, saveReport, get_user_id_and_bounding_box, get_email_by_id, get_latest_report_by_user_id, get_all_reports
from predict import predict_disease
from whisper_transcribe import router as whisper_router
from generateReport import generateReport
import threading

app = FastAPI()

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.start()
user_jobs: Dict[str, str] = {}  # user_id/email -> job_id

# CORS
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserModel(BaseModel):
    name: str
    address: str
    email: str
    phone: str
    location: list

class LoginModel(BaseModel):
    email: str

class LogoutModel(BaseModel):
    id: str

class ChatModel(BaseModel):
    user_id: str
    messages: list
    context: str

class Reports(BaseModel):
    user_id: str
    date: datetime

# Periodic task function
def periodic_task(email: str):
    print(f"Starting report generation for user of email ${email}")
    user_data = get_user_id_and_bounding_box(email)
    if not user_data:
        print(f"[{datetime.now()}] Skipping report generation: User not found for email {email}")
        return

    bounding_box = user_data["bounding_box"]
    user_id = user_data["id"]

    report = generateReport(bounding_box, user_id)
    saveReport(user_id, report)
    print(f"✅ Report generated for {email} (id: {user_id}) at {datetime.now()}")

@app.post("/register")
def register_user(user: UserModel):
    return register(user)

@app.post("/login")
def login_user(data: LoginModel):
    print(f"Login attempt for email: {data.email}")
    email = data.email
    if email in user_jobs:
        print(f"User {email} already logged in, skipping task scheduling.")
        return {"message": "User already logged in and task is running."}
    print(f"Scheduling periodic task for user: {email}")
    job_id = str(uuid4())
    scheduler.add_job(
        periodic_task,
        "cron",
        hour=5,
        minute=0,
        args=[email],
        id=job_id,
        replace_existing=True
    )
    # periodic_task(email)  # Run immediately for the first time

    print(f"Scheduled job ID {job_id} for user {email}")
    user_jobs[email] = job_id
    print(f"User {email} logged in successfully.")

    threading.Thread(target=periodic_task, args=(email,), daemon=True).start()

    return login(data.dict())

@app.post("/logout")
def logout_user(data: LogoutModel):
    id = get_email_by_id(data.id)
    job_id = user_jobs.get(id)
    if not job_id:
        raise HTTPException(status_code=404, detail="No active task found for user.")
    
    try:
        scheduler.remove_job(job_id)
        del user_jobs[id]
        return {"message": f"Logged out {id}, task cancelled."}
    except JobLookupError:
        raise HTTPException(status_code=500, detail="Failed to cancel task.")

@app.post("/chat/{input}")
def chat_with_input(input: str):
    print(f"Received input: {input}")
    response = returnResponse(input)
    return {"response": response}

@app.post("/reset")
def reset_chat(chat: ChatModel):
    saveTheChat(chat)
    resetConversation()
    return {"message": "Conversation reset successfully"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")
    try:
        img_bytes = await file.read()
        disease = predict_disease(img_bytes)
        response_markdown = image_response(disease)
        return {
            "disease": disease,
            "response": response_markdown
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/allReports/{id}")
def get_all(id: str):
    return {"reports": get_all_reports(id)}


app.include_router(whisper_router)

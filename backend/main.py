from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chatbot import returnResponse, resetConversation
from database import register, login
from predict import predict_disease
from chatbot import image_response
from whisper_transcribe import router as whisper_router
from database import register, login, saveTheChat
from predict import predict_disease
from chatbot import image_response

app = FastAPI()

# CORS origins - for local frontend development
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for API requests
class UserModel(BaseModel):
    name: str
    address: str
    email: str
    phone: str
    location: list

class LoginModel(BaseModel):
    email: str

class ChatModel(BaseModel):
    user_id: str
    messages: list
    context: str

@app.post("/chat/{input}")
def chat_with_input(input: str):
    print(f"Received input: {input}")
    response = returnResponse(input)
    return {"response": response}

@app.post("/reset")
def reset_chat(chat : ChatModel):
    saveTheChat(chat)
    resetConversation()
    return {"message": "Conversation reset successfully"}

@app.post("/register")
def register_user(user: UserModel):
    return register(user)

@app.post("/login")
def login_user(data: LoginModel):
    return login(data.dict())

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

app.include_router(whisper_router)
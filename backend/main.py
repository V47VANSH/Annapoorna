from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import returnResponse, resetConversation
from database import register, login

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

# API ROUTES

@app.post("/chat/{input}")
def chat_with_input(input: str):
    response = returnResponse(input)
    return {"response": response}

@app.post("/reset")
def reset_chat():
    resetConversation()
    return {"message": "Conversation reset successfully"}

@app.post("/register")
def register_user(user: UserModel):
    return register(user)

@app.post("/login")
def login_user(data: LoginModel):
    return login(data.dict())

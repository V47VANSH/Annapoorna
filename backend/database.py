from pydantic import BaseModel
from pymongo import MongoClient
from typing import List
from chatbot import returnResponse


client = MongoClient("mongodb://localhost:27017/Drona")
db = client["Annapoorna"]
profile_collection = db["Profiles"]
chat_collection= db["Chats"]

class UserModel(BaseModel):
    name: str
    address: str
    email: str
    phone: str
    location: List[float]

class ChatModel(BaseModel):
    user_id: str
    name: str
    messages: List[dict]
    context: str

def register(user: UserModel):
    existing = profile_collection.find_one({"email": user.email})
    if existing:
        return {"error": "User already exists."}

    # Validate bounding box length (optional but good practice)
    if not isinstance(user.location, list) or len(user.location) != 4:
        return {"error": "Invalid location data. Expected bounding box with 4 values."}

    result = profile_collection.insert_one({
        "name": user.name,
        "address": user.address,
        "email": user.email,
        "phone": user.phone,
        "bounding_box": user.location,  # ✅ renamed for clarity
        "collection_name": ""
    })

    collection_name = str(result.inserted_id)
    profile_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"collection_name": collection_name + "collection"}}
    )

    return {"message": "User registered", "id": collection_name}


def login(data: dict):
    user = profile_collection.find_one({"email": data["email"]})
    if not user:
        return {"error": "User not found"}
    return {"message": "Login successful", "id": str(user["_id"])}

def saveTheChat(chat: ChatModel):
    if len(chat.messages)==1:
        return {"message": "No chat done, not saving!"}
    name= returnResponse("Give a one line name for this chat that we did. It must be one line only and that is really necessary!!!")
    chat_collection.insert_one({
        "user_id":chat.user_id,
        "name": name,
        "messages": chat.messages,
        "context": chat.context
    })
    return {"message": "Chat saved successfully", "name": name}
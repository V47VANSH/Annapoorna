from pydantic import BaseModel
from pymongo import MongoClient
from typing import List
from chatbot import returnResponse
from datetime import datetime
from fastapi import HTTPException
from bson.json_util import dumps
from bson import ObjectId
import json 



client = MongoClient("mongodb://localhost:27017/Drona")
db = client["Annapoorna"]
profile_collection = db["Profiles"]
chat_collection= db["Chats"]
report_collection=db["Reports"]
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

class ReportModel(BaseModel):
    user_id: str
    date : datetime
    report : str

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

def saveReport(user_id: str, report: str):
    now=datetime.now()
    report_collection.insert_one({
        "user_id": user_id,
        "date": now,
        "report" : report
    })

def get_user_id_and_bounding_box(email: str):
    user = profile_collection.find_one({"email": email}, {"_id": 1, "bounding_box": 1})
    if not user:
        return None  # or raise an exception if preferred
    
    return {
        "id": str(user["_id"]),
        "bounding_box": user.get("bounding_box")
    }

def get_email_by_id(user_id: str):
    try:
        user = profile_collection.find_one({"_id": ObjectId(user_id)}, {"email": 1})
        if user:
            return user.get("email")
        else:
            return None
    except Exception as e:
        print(f"Error fetching email for ID {user_id}: {e}")
        return None
    
def get_latest_report_by_user_id(user_id: str):
    try:
        latest_report = report_collection.find_one(
            {"user_id": user_id},
            sort=[("date", -1)]  # Sort by date descending
        )
        if latest_report:
            return {
                "date": latest_report["date"],
                "report": latest_report["report"]
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching latest report for user {user_id}: {e}")
        return None
    
def get_all_reports(user_id: str):
    cursor = report_collection.find({"user_id": user_id}).sort("date", -1)
    reports = list(cursor)
    return json.loads(dumps(reports))

def get_chats_by_user_id(user_id: str):
    try:
        chats = list(chat_collection.find({"user_id": user_id}))
        for chat in chats:
            chat["_id"] = str(chat["_id"])  # Convert ObjectId to string
        return chats
    except Exception as e:
        print(f"Error fetching chats for user {user_id}: {e}")
        return []
    
def get_chat_by_id(chat_id: str):
    try:
        chat = chat_collection.find_one({"_id": ObjectId(chat_id)})
        if not chat:
            return None
        chat["_id"] = str(chat["_id"])  # Convert ObjectId to string
        return chat
    except Exception as e:
        print(f"Error fetching chat by ID {chat_id}: {e}")
        return None

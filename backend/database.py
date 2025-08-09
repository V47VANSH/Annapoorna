"""MongoDB access layer for profiles, chats and generated field reports."""

import json
import logging
from datetime import UTC, datetime

from bson import ObjectId
from bson.errors import InvalidId
from bson.json_util import dumps
from pydantic import BaseModel
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

import config
import memory_store
from chatbot import returnResponse

logger = logging.getLogger(__name__)


def _connect():
    """Return (database, is_persistent).

    MongoClient connects lazily, so ping to check the server is really up.
    If it isn't, use the in-memory store.
    """
    # never touch a real database in offline mode (tests)
    if config.OFFLINE_MODE:
        return memory_store.InMemoryDatabase(), False

    try:
        client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        logger.info("Connected to MongoDB at %s", config.MONGODB_DB_NAME)
        return client[config.MONGODB_DB_NAME], True
    except PyMongoError as exc:
        if not config.ALLOW_KEYLESS_FALLBACKS:
            raise
        logger.warning(
            "MongoDB unreachable (%s); using the in-memory store. "
            "Data will not survive a restart.",
            exc.__class__.__name__,
        )
        return memory_store.InMemoryDatabase(), False


db, IS_PERSISTENT = _connect()
profile_collection = db["Profiles"]
chat_collection = db["Chats"]
report_collection = db["Reports"]


def ensure_indexes() -> None:
    """Create indexes (safe to run more than once)."""
    profile_collection.create_index("email", unique=True)
    report_collection.create_index([("user_id", 1), ("date", DESCENDING)])
    chat_collection.create_index("user_id")


def seed_demo_user() -> str | None:
    """Create the demo farmer if missing and return its id."""
    if not config.DEMO_MODE:
        return None

    demo_id = _to_object_id(config.DEMO_USER_ID)
    if demo_id is None:
        logger.warning("DEMO_USER_ID is not a valid ObjectId; skipping demo seed.")
        return None

    if profile_collection.find_one({"_id": demo_id}):
        return str(demo_id)

    # a field near Ludhiana, Punjab
    profile_collection.insert_one(
        {
            "_id": demo_id,
            "name": "Demo Farmer",
            "address": "Ludhiana, Punjab, India",
            "email": "demo@annapoorna.local",
            "phone": "+91 00000 00000",
            "bounding_box": [30.85, 30.95, 75.80, 75.90],
            "collection_name": f"{demo_id}collection",
            "is_demo": True,
            "created_at": datetime.now(UTC),
        }
    )
    logger.info("Seeded demo user %s", demo_id)
    return str(demo_id)


class UserModel(BaseModel):
    name: str
    address: str
    email: str
    phone: str
    location: list[float]


class ChatModel(BaseModel):
    user_id: str
    messages: list[dict]
    context: str


class ReportModel(BaseModel):
    user_id: str
    date: datetime
    report: str


def _to_object_id(value: str) -> ObjectId | None:
    """Parse a hex id, returning None instead of raising on malformed input."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def register(user: UserModel):
    existing = profile_collection.find_one({"email": user.email})
    if existing:
        return {"error": "User already exists."}

    if not isinstance(user.location, list) or len(user.location) != 4:
        return {"error": "Invalid location data. Expected bounding box with 4 values."}

    result = profile_collection.insert_one(
        {
            "name": user.name,
            "address": user.address,
            "email": user.email,
            "phone": user.phone,
            "bounding_box": user.location,
            "collection_name": "",
            "created_at": datetime.now(UTC),
        }
    )

    user_id = str(result.inserted_id)
    profile_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"collection_name": f"{user_id}collection"}},
    )

    return {"message": "User registered", "id": user_id}


def login(data: dict):
    user = profile_collection.find_one({"email": data["email"]})
    if not user:
        return {"error": "User not found"}
    return {"message": "Login successful", "id": str(user["_id"])}


def saveTheChat(chat: ChatModel):
    """Persist a finished conversation, titled by the model itself."""
    if len(chat.messages) <= 1:
        return {"message": "No chat done, not saving!"}

    try:
        name = returnResponse(
            "Give a one line name for this chat that we did. It must be one line "
            "only and that is really necessary!!!",
            session_id=chat.user_id,
            allow_fallback=False,
        )
    except Exception as exc:
        # still save the chat if naming it fails
        logger.warning("Could not auto-name chat: %s", exc)
        name = f"Chat on {datetime.now(UTC):%Y-%m-%d %H:%M}"

    chat_collection.insert_one(
        {
            "user_id": chat.user_id,
            "name": name,
            "messages": chat.messages,
            "context": chat.context,
            "created_at": datetime.now(UTC),
        }
    )
    return {"message": "Chat saved successfully", "name": name}


def saveReport(user_id: str, report: str):
    report_collection.insert_one(
        {
            "user_id": user_id,
            "date": datetime.now(UTC),
            "report": report,
        }
    )


def get_user_id_and_bounding_box(email: str):
    user = profile_collection.find_one({"email": email}, {"_id": 1, "bounding_box": 1})
    if not user:
        return None

    return {"id": str(user["_id"]), "bounding_box": user.get("bounding_box")}


def get_email_by_id(user_id: str):
    object_id = _to_object_id(user_id)
    if object_id is None:
        return None
    user = profile_collection.find_one({"_id": object_id}, {"email": 1})
    return user.get("email") if user else None


def get_profile_by_id(user_id: str):
    object_id = _to_object_id(user_id)
    if object_id is None:
        return None
    return profile_collection.find_one({"_id": object_id})


def get_latest_report_by_user_id(user_id: str):
    latest_report = report_collection.find_one(
        {"user_id": user_id}, sort=[("date", DESCENDING)]
    )
    if not latest_report:
        return None
    return {"date": latest_report["date"], "report": latest_report["report"]}


def get_all_reports(user_id: str):
    cursor = report_collection.find({"user_id": user_id}).sort("date", DESCENDING)
    return json.loads(dumps(list(cursor)))


def get_chats_by_user_id(user_id: str):
    chats = list(chat_collection.find({"user_id": user_id}))
    for chat in chats:
        chat["_id"] = str(chat["_id"])
    return chats


def get_chat_by_id(chat_id: str):
    object_id = _to_object_id(chat_id)
    if object_id is None:
        return None
    chat = chat_collection.find_one({"_id": object_id})
    if not chat:
        return None
    chat["_id"] = str(chat["_id"])
    return chat

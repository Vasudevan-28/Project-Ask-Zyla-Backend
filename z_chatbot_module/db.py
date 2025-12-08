from __future__ import annotations
import os, time
from typing import Any, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

_client: AsyncIOMotorClient | None = None

def mongo() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"), uuidRepresentation="standard")
    return _client

async def db():
    return mongo()[os.getenv("MONGODB_DB", "skincare_rag")]

async def setdb():
    return mongo()["settings_zyla"]

async def ensure_indexes():
    d = await db()
    # users
    await d.users.create_index("uid", unique=True)
    await d.users.create_index("api_key", unique=True, sparse=True)
    # conversations
    await d.conversations.create_index([("uid", ASCENDING), ("updated_at", DESCENDING)])
    # messages
    await d.messages.create_index([("uid", ASCENDING), ("conversation_id", ASCENDING), ("created_at", ASCENDING)])
    # profiles
    await d.profiles.create_index("uid", unique=True)
    # summaries
    await d.summaries.create_index([("uid", ASCENDING), ("conversation_id", ASCENDING)], unique=True)

from datetime import datetime

async def now_ts() -> float:
    # return time.time()
    return str(datetime.now())

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

db = mongo()["team_zyla"]
bkdb = mongo()["team_zyla_backup"]
users_col = db["users"] 
skin_col = db["skinData"]

backup_users = bkdb["users_del"]


from datetime import datetime

async def now_ts() -> float:
    # return time.time()
    return str(datetime.now())

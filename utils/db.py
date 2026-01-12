from __future__ import annotations
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

_client: AsyncIOMotorClient | None = None

def mongo() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"), uuidRepresentation="standard")
    return _client


def get_db():
    return mongo()[os.getenv("MONGODB_DB", "skincare_rag")]

def get_setdb():
    return mongo()["settings_zyla"]

def get_bkdb():
    return mongo()["team_zyla_backup"]

# def users_col():
#     return get_db()["users"]

# def skin_col():
#     return get_db()["skinData"]

# def user_del_col():
#     return bkdb()["users_del"]

# db = mongo()["team_zyla"]
# bkdb = mongo()["team_zyla_backup"]
# users_col = db["users"] 
# skin_col = db["skinData"]

# backup_users = get_bkdb["users_del"]




async def now_ts() -> float:
    return str(datetime.now())

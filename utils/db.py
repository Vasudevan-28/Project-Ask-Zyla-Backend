# from pymongo import MongoClient
# from dotenv import load_dotenv
# import os

# load_dotenv()  # Load MongoDB URI from .env file

# # MONGO_URI = os.getenv("MONGO_URI")

# # MONGO_URI = "mongodb+srv://saravanan_db:Saravanan@cluster0.2r4wahi.mongodb.net/?appName=Cluster0"
# MONGO_URI = "mongodb+srv://Nobita_arsenal22:NobiArsenal22@arsenal.gxivry5.mongodb.net/?appName=Arsenal"

# client = MongoClient(MONGO_URI)

# db = client["auth_flow"]    # database name
# users_col = db["users"]     # collection name


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
        # _client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"), uuidRepresentation="standard")
        _client = AsyncIOMotorClient("mongodb+srv://Nobita_arsenal22:NobiArsenal22@arsenal.gxivry5.mongodb.net/?appName=Arsenal", uuidRepresentation="standard")
    return _client

db = mongo()["team_zyla"]    # database name
users_col = db["users"] 
skin_col = db["skinData"]


# async def db():
#     return mongo()[os.getenv("MONGODB_DB", "team_zyla_bk")]

# async def ensure_indexes():
#     d = await db()
#     # users
#     await d.users.create_index("uid", unique=True)
#     await d.users.create_index("api_key", unique=True, sparse=True)
#     # conversations
#     await d.conversations.create_index([("uid", ASCENDING), ("updated_at", DESCENDING)])
#     # messages
#     await d.messages.create_index([("uid", ASCENDING), ("conversation_id", ASCENDING), ("created_at", ASCENDING)])
#     # profiles
#     await d.profiles.create_index("uid", unique=True)
#     # summaries
#     await d.summaries.create_index([("uid", ASCENDING), ("conversation_id", ASCENDING)], unique=True)

from datetime import datetime

async def now_ts() -> float:
    # return time.time()
    return str(datetime.now())

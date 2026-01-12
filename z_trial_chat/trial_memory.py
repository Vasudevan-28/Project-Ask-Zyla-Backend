from __future__ import annotations
import json, time
from typing import List, Dict, Any, Optional
from bson import ObjectId
from utils.db import get_db, now_ts
from utils.redis_client import redis

RECENT_N = 8

def redis_key_recent(conversation_id: str) -> str:
    return f"trial_chat:{conversation_id}:recent"

async def create_conversation(uid: str, title: str) -> str:
    d = get_db()
    now = await now_ts()
    res = await d.conversations.insert_one({"uid": uid, "title": (title or "New chat")[:80], "archived": False, "created_at": now, "updated_at": now})
    return str(res.inserted_id)

async def touch_conversation(uid: str, conversation_id: str):
    d = get_db()
    await d.conversations.update_one({"_id": ObjectId(conversation_id), "uid": uid}, {"$set": {"updated_at": await now_ts()}, "$inc": {"turns": 1}})
    conv = await d.conversations.find_one({"_id": ObjectId(conversation_id), "uid": uid})
    turns = conv.get("turns", 0)
    title = conv.get("title", "New chat")
    return {
        "turns": turns,
        "title": title
    }

async def add_message(uid: str, conversation_id: str, role: str, content: str) -> str:
    d = get_db()
    doc = {"uid": uid, "conversation_id": ObjectId(conversation_id), "role": role, "content": content, "created_at": await now_ts()}
    res = await d.messages.insert_one(doc)
    
    entry = json.dumps({"role": role, "content": content})
    key = redis_key_recent(conversation_id)
    await redis.rpush(key, entry)
    await redis.ltrim(key, -RECENT_N, -1)  
    return str(res.inserted_id)

async def get_recent_messages(conversation_id: str, fallback_from_mongo: bool = True) -> List[Dict[str, str]]:
    key = redis_key_recent(conversation_id)
    items = await redis.lrange(key, -RECENT_N, -1)
    if items:
        return [json.loads(x) for x in items]
    if not fallback_from_mongo:
        return []

    d = get_db()
    cur = d.messages.find({"conversation_id": ObjectId(conversation_id)}).sort("created_at", -1).limit(RECENT_N)
    out = []
    async for m in cur:
        out.append({"role": m["role"], "content": m["content"]})
    out.reverse()
    if out:
        await redis.delete(key)
        for m in out:
            await redis.rpush(key, json.dumps(m))
    return out

async def get_messages(uid: str, conversation_id: str) -> List[Dict[str, Any]]:
    d = get_db()
    ok = await d.conversations.find_one({"_id": ObjectId(conversation_id), "uid": uid})
    if not ok:
        return []
    cur = d.messages.find({"conversation_id": ObjectId(conversation_id), "uid": uid}).sort("created_at", 1)
    out = []
    async for m in cur:
        # out.append({"id": str(m["_id"]), "role": m["role"], "content": m["content"], "hits": m["hits"], "created_at": m["created_at"]})
        out.append({"id": str(m["_id"]), "role": m["role"], "content": m["content"],"created_at": m["created_at"]})
    return out

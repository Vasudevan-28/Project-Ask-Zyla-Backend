from __future__ import annotations
import json, time
from typing import List, Dict, Any, Optional
from bson import ObjectId
from z_chatbot_module.db import db, now_ts
from z_chatbot_module.redis_client import redis

RECENT_N = 8

def redis_key_recent(conversation_id: str) -> str:
    # return f"conv:{conversation_id}:recent"
    # return f"zyla_proto:{conversation_id}:recent"
    return f"team_zyla:{conversation_id}:recent"

# async def get_profile(uid: str) -> Dict[str, Any]:
#     d = await db()
#     doc = await d.profiles.find_one({"uid": uid})
#     if not doc:
#         return {"name": None, "skin_type": None, "concerns": [], "allergies": [], "avoid_ingredients": [],
#                 "prefer_ingredients": [], "budget_max": None, "fragrance_free": None}
#     return doc.get("profile", {})

# async def patch_profile(uid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
#     d = await db()
#     current = await get_profile(uid)
#     merged = {**current}
#     for k, v in patch.items():
#         if v is None:
#             merged[k] = None
#         elif isinstance(v, list):
#             merged[k] = list(dict.fromkeys([x for x in v if x is not None and x != ""]))
#         else:
#             merged[k] = v
#     now = await now_ts()
#     await d.profiles.update_one({"uid": uid}, {"$set": {"profile": merged, "updated_at": now}, "$setOnInsert": {"uid": uid, "created_at": now}}, upsert=True)
#     return merged

async def create_conversation(uid: str, title: str) -> str:
    d = await db()
    now = await now_ts()
    res = await d.conversations.insert_one({"uid": uid, "title": (title or "New chat")[:80], "archived": False, "created_at": now, "updated_at": now})
    return str(res.inserted_id)

async def create_archive_conversation(uid: str, title: str) -> str:
    d = await db()
    now = await now_ts()
    res = await d.conversations.insert_one({"uid": uid, "title": (title or "New chat")[:80], "archived": True, "created_at": now, "updated_at": now})
    return str(res.inserted_id)

async def touch_conversation(uid: str, conversation_id: str):
    d = await db()
    await d.conversations.update_one({"_id": ObjectId(conversation_id), "uid": uid}, {"$set": {"updated_at": await now_ts()}, "$inc": {"turns": 1}})
    conv = await d.conversations.find_one({"_id": ObjectId(conversation_id), "uid": uid})
    turns = conv.get("turns", 0)
    title = conv.get("title", "New chat")
    return {
        "turns": turns,
        "title": title
    }

async def add_message(uid: str, conversation_id: str, role: str, content: str) -> str:
    d = await db()
    # doc = {"uid": uid, "conversation_id": ObjectId(conversation_id), "hits" : hits, "role": role, "content": content, "created_at": await now_ts()}
    doc = {"uid": uid, "conversation_id": ObjectId(conversation_id),  "role": role, "content": content, "created_at": await now_ts()}
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

    d = await db()
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

async def list_conversations(uid: str) -> List[Dict[str, Any]]:
    d = await db()
    cur = d.conversations.find({"uid": uid, "archived": False}).sort("updated_at", -1)
    out = []
    async for c in cur:
        out.append({"id": str(c["_id"]), "title": c.get("title", "Untitled"), "updated_at": c.get("updated_at", 0.0)})
    return out

async def list_archived_conversations(uid: str) -> List[Dict[str, Any]]:
    d = await db()
    cur = d.conversations.find({"uid": uid, "archived": True}).sort("updated_at", -1)
    out = []
    async for c in cur:
        out.append({"id": str(c["_id"]), "title": c.get("title", "Untitled"), "updated_at": c.get("updated_at", 0.0)})
    return out

async def get_messages(uid: str, conversation_id: str) -> List[Dict[str, Any]]:
    d = await db()
    ok = await d.conversations.find_one({"_id": ObjectId(conversation_id), "uid": uid})
    if not ok:
        return []
    cur = d.messages.find({"conversation_id": ObjectId(conversation_id), "uid": uid}).sort("created_at", 1)
    out = []
    async for m in cur:
        # out.append({"id": str(m["_id"]), "role": m["role"], "content": m["content"], "hits": m["hits"], "created_at": m["created_at"]})
        out.append({"id": str(m["_id"]), "role": m["role"], "content": m["content"], "created_at": m["created_at"]})
    return out

# async def put_favourites(favs : Dict[str, any], uid: str):
#     fdb = await db()
#     # ok = await fdb.favourites.insert_one(favs)  
#     # fdoc =  {"uid" : uid, "product_name" : favs["product_name"], "price" : favs["price"],
#     #                                        "type" : favs["category"], "url": favs["url"], "clean_ingreds" : favs["clean_ingreds"]
#     #                                        }
    
#     fdoc = {"uid" : uid, **favs}
#     fok = await fdb.favourites.insert_one(fdoc)
#     # return fok
#     return {"inserted_id": str(fok.inserted_id)}

# async def get_favourites(uid):
#     fdb = await db()
#     ok = fdb.favourites.find({"uid" : uid})
    
#     if not ok:
#         return []
#     fp = []
#     async for f in ok:
#         fp.append({"id" : str(f["_id"]), "product_name" : f["product_name"], "price" : f["price"], "type" : f["category"], "url": f["url"], "clean_ingreds" : f["clean_ingreds"]})
        
#     return fp

# async def delete_favorites(favs: Dict[str, any], uid:str):
    dfdb = await db()
    
    query = {"uid" : uid, "product_name": favs["product_name"]}
    
    res = await dfdb.favourites.delete_one(query)
    
    if res.deleted_count > 0:
        return {"status" : "Product is removed from Favorites"}
    else:
        return {"status" : "Product is not removed from Favorites"}
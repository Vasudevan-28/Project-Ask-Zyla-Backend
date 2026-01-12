
from __future__ import annotations
from fastapi import Depends, APIRouter
from bson import ObjectId
from utils.db import get_db, now_ts

from z_chatbot_module.schemas import ConversationCreate

from z_chatbot_module.memory import (
    create_conversation, create_archive_conversation, list_conversations, list_archived_conversations, get_messages, 
)
from utils._auth_firebase import auth_user_fb


conversation_router = APIRouter()

@conversation_router.post("/conversations")
async def conversations_create(body: ConversationCreate, user=Depends(auth_user_fb)):
    cid = await create_conversation(user["uid"], body.title or "New chat")
    return {"id": cid}

@conversation_router.post("/archive/conversations")
async def archive_conversations_create(body: ConversationCreate, user=Depends(auth_user_fb)):
    cid = await create_archive_conversation(user["uid"], body.title or "New chat")
    return {"id": cid}

@conversation_router.get("/conversations")
async def conversations_list(user=Depends(auth_user_fb)):
    return await list_conversations(user["uid"])

@conversation_router.get("/conversations/archived")
async def conversations_list_archived(user=Depends(auth_user_fb)):
    return await list_archived_conversations(user["uid"])

@conversation_router.get("/conversations/{conversation_id}/messages")
async def conversations_messages(conversation_id: str, user=Depends(auth_user_fb)):
    return await get_messages(user["uid"], conversation_id)


@conversation_router.post("/conversations/{cid}/rename")
async def conversations_rename(cid: str, body: dict, user=Depends(auth_user_fb)):
    new_title = body.get("title", "").strip()[:80]
    d = get_db()

    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"title": new_title, "updated_at": await now_ts()}}
    )

    return {"status": "ok"}

@conversation_router.post("/conversations/{cid}/archive")
async def conversations_archive(cid: str, user=Depends(auth_user_fb)):
    d = get_db()
    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"archived": True, "updated_at": await now_ts()}}
    )
    return {"status": "ok"}

@conversation_router.post("/conversations/{cid}/unArchive")
async def conversations_unarchive(cid: str, user=Depends(auth_user_fb)):
    d = get_db()
    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"archived": False, "updated_at": await now_ts()}}
    )
    return {"status": "ok"}

@conversation_router.delete("/conversations/{cid}")
async def conversations_delete(cid: str, user=Depends(auth_user_fb)):
    d = get_db()
    await d.conversations.delete_one(
        {"_id": ObjectId(cid), "uid": user["uid"]}
    )
    return {"status": "deleted"}
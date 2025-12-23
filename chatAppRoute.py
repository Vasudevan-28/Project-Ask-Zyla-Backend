from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Depends, Header, Response, APIRouter
# from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from groq import Groq

from bson import ObjectId
from z_chatbot_module.db import db, now_ts

from z_chatbot_module.schemas import ConversationCreate, ChatRequest, ChatResponse, ProfilePatch, Profile, SkinProfileWrapper, TrialChatRequest, TrialChatResponse

from z_chatbot_module.memory import (
    create_conversation, list_conversations, list_archived_conversations, get_messages, 
)
from z_chatbot_module.chat_graph import build_chat_graph
from z_chatbot_module._auth_firebase import  auth_user_fb



load_dotenv()

# app = FastAPI(title="Ask Zyla Auth", version="1.0.0")

chatApp = APIRouter(prefix="/chatApp", tags=["chat app"])

# chatApp.include_router(appAuth)


@chatApp.get("/testAPI")
def testingApi():
    return {"testing": "okay"}



@chatApp.post("/conversations")
async def conversations_create(body: ConversationCreate, user=Depends(auth_user_fb)):
    cid = await create_conversation(user["uid"], body.title or "New chat")
    return {"id": cid}

@chatApp.get("/conversations")
async def conversations_list(user=Depends(auth_user_fb)):
    return await list_conversations(user["uid"])

@chatApp.get("/conversations/archived")
async def conversations_list_archived(user=Depends(auth_user_fb)):
    return await list_archived_conversations(user["uid"])

@chatApp.get("/conversations/{conversation_id}/messages")
async def conversations_messages(conversation_id: str, user=Depends(auth_user_fb)):
    return await get_messages(user["uid"], conversation_id)


@chatApp.post("/conversations/{cid}/rename")
async def conversations_rename(cid: str, body: dict, user=Depends(auth_user_fb)):
    new_title = body.get("title", "").strip()[:80]
    d = await db()

    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"title": new_title, "updated_at": await now_ts()}}
    )

    return {"status": "ok"}

@chatApp.post("/conversations/{cid}/archive")
async def conversations_archive(cid: str, user=Depends(auth_user_fb)):
    d = await db()
    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"archived": True, "updated_at": await now_ts()}}
    )
    return {"status": "ok"}

@chatApp.post("/conversations/{cid}/unArchive")
async def conversations_archive(cid: str, user=Depends(auth_user_fb)):
    d = await db()
    await d.conversations.update_one(
        {"_id": ObjectId(cid), "uid": user["uid"]},
        {"$set": {"archived": False, "updated_at": await now_ts()}}
    )
    return {"status": "ok"}

@chatApp.delete("/conversations/{cid}")
async def conversations_delete(cid: str, user=Depends(auth_user_fb)):
    d = await db()
    await d.conversations.delete_one(
        {"_id": ObjectId(cid), "uid": user["uid"]}
    )
    return {"status": "deleted"}


chat_app = build_chat_graph()

@chatApp.post("/chatgraph", response_model=ChatResponse)
async def chat(req: ChatRequest, user=Depends(auth_user_fb)):
    uid = user["uid"]

    initial_state = {
        "uid": uid,
        "conversation_id": req.conversation_id,
        "message": req.message,
    }

    final_state = await chat_app.ainvoke(initial_state)

    return ChatResponse(
        conversation_id=final_state["conversation_id"],
        reply=final_state["reply"],
        # intent_query = final_state["intent_query"],
        # hits=final_state.get("hits", []),
        # intent_recommend=bool(final_state.get("intent_recommend", False)),
        used_messages=final_state.get("used_messages", []),
        # profile_used=Profile(**final_state.get("profile", {})),
        user_profile=final_state["user_profile"],
        summary=final_state.get("summary", "") or "",
    )
    
from z_chatbot_module.guest_session import TrialSession, get_trial_session
from z_chatbot_module.chat_graph import build_trial_chat_graph
from z_chatbot_module.schemas import TrialUserChkResponse

trialChat = build_trial_chat_graph()

@chatApp.post("/trial/chat/trialUser")
async def trial_chk(session: TrialSession = Depends(get_trial_session), response: Response = None):
    if session.remaining_trials <= 0:
        raise HTTPException(
            status_code = 402,
            detail={
              "code": "TRIAL_EXHAUSTED",
                "message": "Your free trial is over. Please sign up to continue chatting.",   
            }
        )
        
    new_chat_count = session.chat_count
    new_remaining = max(0, 3 - new_chat_count)
    trial_exhausted = new_remaining == 0

    if response is not None:
        response.set_cookie(
            key="trial_id",
            value=session.guest_id,
            max_age=60 * 60 * 24 * 7, 
            httponly=True,
            samesite="lax",
        )

    uid = f"guest:{session.guest_id}"

    
    return TrialUserChkResponse(
        guest_id=uid,
        remaining_trials=new_remaining,
        trials_exhausted=trial_exhausted
        
    )

@chatApp.post("/trial/chat", response_model=TrialChatResponse)
async def trial_chat(
    req: TrialChatRequest,
    session: TrialSession = Depends(get_trial_session),
    response: Response = None,
):
    d = await db()

    if session.remaining_trials <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "TRIAL_EXHAUSTED",
                "message": "Your free trial is over. Please sign up to continue chatting.",
            },
        )

    new_chat_count = session.chat_count + 1
    new_remaining = max(0, 3 - new_chat_count)

    await d.guest_sessions.update_one(
        {"_id": ObjectId(session.guest_id)},
        {
            "$set": {
                "chat_count": new_chat_count,
                "updated_at": await now_ts(),
            }
        },
    )

    if response is not None:
        response.set_cookie(
            key="trial_id",
            value=session.guest_id,
            max_age=60 * 60 * 24 * 7, 
            httponly=True,
            secure=True,
            samesite="none",
        )

    uid = f"guest:{session.guest_id}"

    initial_state = {
        "guest_id": uid,
        "conversation_id": req.conversation_id,
        "message": req.message,
    }

    final_state = await trialChat.ainvoke(initial_state)

    trial_exhausted = new_remaining == 0

    return TrialChatResponse(
        conversation_id=final_state["conversation_id"],
        reply=final_state["reply"],
        remaining_trials=new_remaining,
        trials_exhausted=trial_exhausted,
    )

    
    


@chatApp.get("/skin-profile/{user_id}")
async def get_skin_profile(user_id: str):
    
    spdb = await db()
    
    # doc = await spdb.skinData.find_one({"skinProfileData.userId": user_id})
    doc = await spdb.skinData.find_one({"userId": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # cleared = doc.get("cleared", False)
    
    # if cleared:
    #     raise HTTPException(status_code=404, detail="data is cleared")     

    doc["_id"] = str(doc["_id"])
    return doc


from datetime import datetime

@chatApp.put("/skin-answers-add/{user_id}")
async def add_skin_answers(user_id: str, data: SkinProfileWrapper):
    spdb = await db()

    body = data.skinProfileData.model_dump()

    user = await spdb.users.find_one(
        {"firebase_uid": user_id},
        {"name": 1, "dob": 1, "gender": 1}  
    )

    if not user:
        return {"error": "User not found"}

    def calculate_age(dob_str):
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    age = calculate_age(user["dob"])

    body["userId"] = user_id
    body["name"] = user["name"]
    body["gender"] = user["gender"]
    body["age"] = age  

    # existing = await spdb.skinData.find_one({"skinProfileData.userId": user_id})
    existing = await spdb.skinData.find_one({"userId": user_id})

    if not existing:
        await spdb.skinData.insert_one({"skinProfileData": body, "userId" : user_id, "cleared" : False})
        await spdb.users.update_one({"firebase_uid" : user_id},
                                {"$set": {"skin_profile" : True}})
        return {"message": "Skin profile created successfully"}

    # result = await spdb.skinData.update_one(
    #     {"skinProfileData.userId": user_id},
    #     {"$set": {"skinProfileData": body}}
    # )
    result = await spdb.skinData.update_one(
        {"userId": user_id},
        {"$set": {"skinProfileData": body, "userId" : user_id, "cleared" : False}}
    )
    
    await spdb.users.update_one({"firebase_uid" : user_id},
                                {"$set": {"skin_profile" : True}})

    if result.modified_count == 0:
        return {"message": "No changes made, profile already up to date"}

    return {"message": "Skin profile updated successfully"}




import json

from z_chatbot_module.llm_core import call_groq_model

def calculate_age(dob_str: str) -> int:
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


@chatApp.put("/skin-profile/{user_id}")
async def update_skin_profile(user_id: str, data: SkinProfileWrapper):
    spdb = await db()

    user = await spdb.users.find_one(
        {"firebase_uid": user_id},
        {"name": 1, "dob": 1, "gender": 1}
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    age = calculate_age(user["dob"])

    base_data = data.skinProfileData.model_dump()

    enriched_data = {
        **base_data,
        "userId": user_id,
        "name": user["name"],
        "gender": user["gender"],
        "age": age,
    }

    prompt = json.dumps(enriched_data)
    description = await call_groq_model(prompt)

    updated_data = {
        **enriched_data,
        "zyla_summary": description,
    }

    await spdb.skinData.update_one(
        {"skinProfileData.userId": user_id},
        {"$set": {"skinProfileData": updated_data}},
        upsert=True,
    )

    saved_doc = await spdb.skinData.find_one(
        {"skinProfileData.userId": user_id},
        {"_id": 0}
    )

    return saved_doc



from __future__ import annotations
from fastapi import Depends, APIRouter

from z_chatbot_module.schemas import  ChatRequest, ChatResponse

from z_chatbot_module.chat_graph import build_chat_graph
from utils._auth_firebase import auth_user_fb


chat_app = build_chat_graph()

chatbot_router = APIRouter(prefix="/chatbot")

@chatbot_router.post("/chatgraph", response_model=ChatResponse)
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
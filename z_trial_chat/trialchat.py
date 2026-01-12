from fastapi import APIRouter, Depends, Response, HTTPException
from bson import ObjectId
from utils.db import get_db, now_ts
from z_trial_chat.guest_session import TrialSession, get_trial_session
from z_trial_chat.trial_chat_graph import build_trial_chat_graph
from z_trial_chat.trial_schemas import TrialChatRequest, TrialChatResponse, TrialUserChkResponse

trial_chat_router = APIRouter(prefix="/trial")

trialChat = build_trial_chat_graph()

@trial_chat_router.post("/chat/trialUser")
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

@trial_chat_router.post("/chat", response_model=TrialChatResponse)
async def trial_chat(
    req: TrialChatRequest,
    session: TrialSession = Depends(get_trial_session),
    response: Response = None,
):
    d = get_db()

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

    
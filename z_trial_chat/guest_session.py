from pydantic import BaseModel
from typing import Optional
from fastapi import Cookie
from bson import ObjectId
from utils.db import get_db, now_ts

MAX_TRIAL_CHATS = 3

class TrialSession(BaseModel):
    guest_id: str
    chat_count: int
    remaining_trials: int
    
async def get_trial_session(trial_id: Optional[str] = Cookie(None)) -> TrialSession:
    d = get_db()

    guest_doc = None
    
    print("TRIAL ID FROM COOKIE: ", trial_id)

    if trial_id:
        try:
            guest_doc = await d.guest_sessions.find_one({"_id": ObjectId(trial_id)})
        except Exception:
            guest_doc = None

    if not guest_doc:
        now = await now_ts()
        res = await d.guest_sessions.insert_one(
            {
                "chat_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        )
        guest_id = str(res.inserted_id)
        chat_count = 0
    else:
        guest_id = str(guest_doc["_id"])
        chat_count = int(guest_doc.get("chat_count", 0))

    remaining = max(0, MAX_TRIAL_CHATS - chat_count)

    return TrialSession(
        guest_id=guest_id,
        chat_count=chat_count,
        remaining_trials=remaining,
    )

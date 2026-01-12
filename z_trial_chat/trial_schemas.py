from pydantic import BaseModel, Field
from typing import Optional

class TrialChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1)

class TrialChatResponse(BaseModel):
    conversation_id: str
    remaining_trials: int
    reply : str
    trials_exhausted: bool
    
class TrialUserChkResponse(BaseModel):
    guest_id: str
    remaining_trials: int
    trials_exhausted: bool


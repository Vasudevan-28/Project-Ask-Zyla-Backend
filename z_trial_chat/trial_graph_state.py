from typing import TypedDict, List, Dict, Any, Optional

class TrialChatState(TypedDict, total=False):
    guest_id : str
    conversation_id: Optional[str]
    message: str

    recent_messages: List[Dict[str, str]]
    
    # LLM
    used_messages: List[Dict[str, str]]
    reply: str

    remaining_trials: int
    trials_exhausted: bool
    
    title:str
    turns: int

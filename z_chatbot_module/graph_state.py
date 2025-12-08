from typing import TypedDict, List, Dict, Any, Optional

class ChatState(TypedDict, total=False):
    uid: str
    conversation_id: Optional[str]
    message: str

    # from intent + RAG
    intent_recommend: bool
    intent: bool
    intent_query: str
    hits: List[Dict[str, Any]]

    # memory
    user_profile: Dict[str, Any]
    profile: Dict[str, Any]
    summary: str
    recent_messages: List[Dict[str, str]]
    
    turns: int
    title: str

    # LLM
    used_messages: List[Dict[str, str]]
    reply: str

    # summarizer
    all_messages: List[Dict[str, Any]]



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

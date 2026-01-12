from typing import TypedDict, List, Dict, Any, Optional

class ChatState(TypedDict, total=False):
    uid: str
    conversation_id: Optional[str]
    message: str

    # memory
    user_profile: Dict[str, Any]
    # profile: Dict[str, Any]
    summary: str
    recent_messages: List[Dict[str, str]]
    
    turns: int
    title: str

    # LLM
    used_messages: List[Dict[str, str]]
    reply: str

    # summarizer
    all_messages: List[Dict[str, Any]]


    # from intent + RAG
    # intent_recommend: Optional[bool]
    # intent: Optional[bool]
    # intent_query: Optional[str]
    # hits: Optional[List[Dict[str, Any]]]

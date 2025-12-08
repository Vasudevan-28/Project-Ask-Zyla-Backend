from typing import Dict, Any

DEFAULT_TOP_K = 2

from z_chatbot_module.trial_memory import create_conversation

async def trial_node_ensure_conversation(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["guest_id"]
    cid = state.get("conversation_id")

    if not cid:
        cid = await create_conversation(uid, "New chat")

    return {"conversation_id": cid}


from z_chatbot_module.trial_memory import add_message

async def trial_node_store_user_message(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["guest_id"]
    cid = state["conversation_id"]
    msg = state["message"]
    
    await add_message(uid=uid, conversation_id=cid, role="user", content=msg)
    return {}


from z_chatbot_module.trial_memory import  get_recent_messages

async def trial_node_load_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["guest_id"]
    cid = state["conversation_id"]

    print("---------------------------------------------------------------------")
    recent = await get_recent_messages(cid, fallback_from_mongo=True)

    return {
        "recent_messages": recent,
    }



from z_chatbot_module.trial_llm_core import build_context_messages, llm_reply

async def trial_node_generate_reply(state: Dict[str, Any]) -> Dict[str, Any]:
    
    recent = state.get("recent_messages", [])
   
    used_messages = build_context_messages(recent)
    reply = llm_reply(used_messages)

    return {
        "used_messages": used_messages,
        "reply": reply,
    }


from z_chatbot_module.memory import touch_conversation

async def trial_node_store_assistant_message(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["guest_id"]
    cid = state["conversation_id"]
    reply = state["reply"]

    await add_message(uid=uid, conversation_id=cid, role="assistant", content=reply)
    conv = await touch_conversation(uid, cid)
    
    return {
        "turns": conv["turns"],
    }

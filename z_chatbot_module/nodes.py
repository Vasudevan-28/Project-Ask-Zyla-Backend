from typing import Dict, Any
# from chroma_lib import embed_texts, needs_recommendation, collection, llm_intent_confirm

DEFAULT_TOP_K = 2

from z_chatbot_module.memory import create_conversation

async def node_ensure_conversation(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state.get("conversation_id")

    if not cid:
        cid = await create_conversation(uid, "New chat")
    return {"conversation_id": cid}


from z_chatbot_module.memory import add_message

async def node_store_user_message(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state["conversation_id"]
    msg = state["message"]
    # hits = []
    await add_message(uid=uid, conversation_id=cid, role="user", content=msg)
    return {}


from z_chatbot_module.memory import  get_recent_messages
# from summarizer import get_summary
from z_chatbot_module.new_summary import get_summary,  get_user_skin_profile

async def node_load_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state["conversation_id"]

    # user_profile = await get_user_profile(uid)
    user_profile = await get_user_skin_profile(uid)
    print(user_profile)
    print("---------------------------------------------------------------------")
    # profile = await get_profile(uid)
    summary = await get_summary(uid, cid)
    recent = await get_recent_messages(cid, fallback_from_mongo=True)

    return {
        "user_profile": user_profile,
        # "profile": profile,
        "summary": summary,
        "recent_messages": recent,
    }



async def node_detect_intent_and_retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    msg = state["message"]
    # intent_reco = needs_recommendation(msg)
    # intent_reco = llm_intent_confirm(state)
    
    # query = intent_reco["query"] if intent_reco["intent"] else state["message"]
    
    # query = "shower oil"
    
    # print(f"Intent Recommend : {intent_reco}")
    # print(f"Intent Query : {query}")
    # print(f"Intent : {intent_reco["intent"]}")
    hits = []
    # if intent_reco["intent"]:
    #     # qvec = embed_texts([msg])[0]
        
    # # try:
    #     print("Trying RAG")
    #     qvec = embed_texts([query])[0]
    #     results = collection.query(
    #         query_embeddings=[qvec],
    #         n_results=DEFAULT_TOP_K,
    #     )
    #     if results and results.get("ids"):
    #         for i in range(len(results["ids"][0])):
    #             hits.append({
    #                 "id": results["ids"][0][i],
    #                 "distance": results.get("distances", [[None]])[0][i],
    #                 "document": results.get("documents", [[None]])[0][i],
    #                 "metadata": results.get("metadatas", [[{}]])[0][i],
    #             })
    # # except:
    # #     hits = []

    # return {
    #     "intent_recommend": intent_reco["intent"],
    #     "intent_query" : intent_reco["query"],
    #     "hits": hits,
    # }
    return {
        "intent_recommend": "hold",
        "intent_query" : "hold",
        "hits": hits,
    }


from z_chatbot_module.llm_core import build_context_messages, llm_reply

async def node_generate_reply(state: Dict[str, Any]) -> Dict[str, Any]:
    # profile = state["profile"]
    user_profile = state["user_profile"]
    summary = state.get("summary", "")
    recent = state.get("recent_messages", [])
    # hits = state.get("hits", [])
    # intent_recommend = bool(state.get("intent_recommend"))

    used_messages = build_context_messages(user_profile, summary, recent)
    # reply = llm_reply(used_messages, hits, intent_recommend and len(hits) > 0)
    reply = llm_reply(used_messages)

    return {
        "used_messages": used_messages,
        "reply": reply,
    }


from z_chatbot_module.memory import touch_conversation

async def node_store_assistant_message(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state["conversation_id"]
    reply = state["reply"]
    # hits = state["hits"] if state["hits"] else []

    # await add_message(uid=uid, conversation_id=cid, hits=hits, role="assistant", content=reply)
    await add_message(uid=uid, conversation_id=cid, role="assistant", content=reply)
    conv = await touch_conversation(uid, cid)
    
    print("TITLE FROM DB: ", conv["title"])
    return {
        "turns": conv["turns"],
        "title": conv["title"]
    }

from z_chatbot_module.llm_core import set_conversation_title

async def node_set_conversation_title(state: Dict[str, Any]) -> Dict[str, Any]:

    turns = state.get("turns", 0)
    title = state.get("title", "New chat")
    
    if (turns < 3) :
        return {}
    # else:
    #     if title == "New chat":
    #     # msgs = List[Dict[str, str]] = []
    #         await set_conversation_title(state)
    #     else:
    #         return
    
    print("TITLE FROM STATE: ", title)

    if title == "New chat":
        return await set_conversation_title(state)
    
    return {}
        

# from memory import get_messages
# from summarizer import summarize_if_needed

# async def node_update_summary(state: Dict[str, Any]) -> Dict[str, Any]:
#     uid = state["uid"]
#     cid = state["conversation_id"]

#     all_msgs_full = await get_messages(uid, cid)
#     all_msgs = [{"role": m["role"], "content": m["content"]} for m in all_msgs_full]
#     new_summary = await summarize_if_needed(uid, cid, all_msgs)

#     return {
#         "summary": new_summary or state.get("summary", ""),
#         "all_messages": all_msgs_full,
#     }

from typing import Dict, Any
from z_chatbot_module.memory import get_messages
from z_chatbot_module.new_summary import (
    summarize_conversation_if_needed,
    update_user_profile_from_summary,
)


async def node_update_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state["conversation_id"]

    all_msgs_full = await get_messages(uid, cid)
    chat_msgs = [{"role": m["role"], "content": m["content"]} for m in all_msgs_full]

    new_summary = await summarize_conversation_if_needed(uid, cid, chat_msgs)

    # updated_profile = await update_user_profile_from_summary(uid, new_summary)

    return {
        **state,
        "summary": new_summary or state.get("summary", ""),
        "user_profile": state.get("user_profile", {}),
        "all_messages": all_msgs_full,
    }

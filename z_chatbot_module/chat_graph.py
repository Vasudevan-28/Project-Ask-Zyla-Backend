from langgraph.graph import StateGraph, END
from z_chatbot_module.graph_state import ChatState
from z_chatbot_module.nodes import (
    node_detect_intent_and_retrieve,
    node_ensure_conversation,
    node_store_user_message,
    node_load_memory,
    node_generate_reply,
    node_store_assistant_message,
    node_set_conversation_title,
    node_update_summary,
    
)



def build_chat_graph():
    graph = StateGraph(ChatState)
   
    graph.add_node("ensure_conversation", node_ensure_conversation)
    graph.add_node("store_user_message", node_store_user_message)
    graph.add_node("load_memory", node_load_memory)
    graph.add_node("detect_intent_and_retrieve", node_detect_intent_and_retrieve)
    graph.add_node("generate_reply", node_generate_reply)
    graph.add_node("store_assistant_message", node_store_assistant_message)
    graph.add_node("set_conversation_title", node_set_conversation_title )
    graph.add_node("update_summary", node_update_summary)

    graph.set_entry_point("ensure_conversation")

    graph.add_edge("ensure_conversation", "store_user_message")
    graph.add_edge("store_user_message", "load_memory")
    graph.add_edge("load_memory", "detect_intent_and_retrieve")
    graph.add_edge("detect_intent_and_retrieve", "generate_reply")
    graph.add_edge("generate_reply", "store_assistant_message")
    graph.add_edge("store_assistant_message", "set_conversation_title")
    graph.add_edge("set_conversation_title", "update_summary")
    graph.add_edge("update_summary", END)

    return graph.compile()

    # graph.add_node("detect_intent_and_retrieve", node_detect_intent_and_retrieve)
    # graph.add_node("ensure_conversation", node_ensure_conversation)
    # graph.add_node("store_user_message", node_store_user_message)
    # graph.add_node("load_memory", node_load_memory)
    # graph.add_node("generate_reply", node_generate_reply)
    # graph.add_node("store_assistant_message", node_store_assistant_message)
    # graph.add_node("update_summary", node_update_summary)

    # graph.set_entry_point("detect_intent_and_retrieve")

    # graph.add_edge("detect_intent_and_retrieve", "ensure_conversation")
    # graph.add_edge("ensure_conversation", "store_user_message")
    # graph.add_edge("store_user_message", "load_memory")
    # graph.add_edge("load_memory", "generate_reply")
    # graph.add_edge("generate_reply", "store_assistant_message")
    # graph.add_edge("store_assistant_message", "update_summary")
    # graph.add_edge("update_summary", END)
    
    
from z_chatbot_module.trial_nodes import ( trial_node_ensure_conversation, trial_node_generate_reply, trial_node_load_memory, trial_node_store_assistant_message, trial_node_store_user_message)
from z_chatbot_module.graph_state import TrialChatState

def build_trial_chat_graph():
    graph = StateGraph(TrialChatState)
    
    graph.add_node("ensure_conversation", trial_node_ensure_conversation)
    graph.add_node("store_user_message", trial_node_store_user_message)
    graph.add_node("load_memory", trial_node_load_memory)
    graph.add_node("generate_reply", trial_node_generate_reply)
    graph.add_node("store_assistant_message", trial_node_store_assistant_message)
    
    graph.set_entry_point("ensure_conversation")
    
    graph.add_edge("ensure_conversation", "store_user_message")
    graph.add_edge("store_user_message", "load_memory")
    graph.add_edge("load_memory", "generate_reply")
    graph.add_edge("generate_reply", "store_assistant_message")
    graph.add_edge("store_assistant_message", END)
    
    return graph.compile()
    
    
    
    
    
    
    
    
    
    
    
    
"""
    ensure_conversation
    store_user_message
    load_memory
    detect_intent_and_retrieve
    generate_reply
    store_assistant_message
    update_summary    
    
"""
    
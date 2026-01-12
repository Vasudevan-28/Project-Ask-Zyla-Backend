from langgraph.graph import StateGraph, END
from z_trial_chat.trial_nodes import ( trial_node_ensure_conversation, trial_node_generate_reply, trial_node_load_memory, trial_node_store_assistant_message, trial_node_store_user_message)
from z_trial_chat.trial_graph_state import TrialChatState

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
    
    
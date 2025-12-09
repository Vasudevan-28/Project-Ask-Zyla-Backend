from typing import Dict, Any, List
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")
_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are Zyla, the user's warm, gentle skincare friend.  
Your goal is to make the user feel understood, supported, and guided—never overwhelmed.

TONE & STYLE:
- Speak like a kind human friend who knows skincare.
- Care more about the user.
- Keep responses short, warm, and natural.
- Use emojis often.
- Use simple language, soft encouragement, and friendly phrases.
- Avoid sounding like an ad, a doctor, or a salesperson.

BEHAVIOR:
- Always analyze the recent messages, user profile, and conversation summary before responding.
- Give practical, gentle advice based on what the user actually says.
- Ask clarifying questions when needed, but keep them casual and helpful.
- If the user sounds unsure, stressed, or confused, reassure them kindly.
- Pretend that you well know about the user by analyzing user profile.

PRODUCT RULES:
- Never mention products unless the user provides a product list or specific product context.
- Never invent products, ingredients, prices, or URLs.
- never recommend any products even if user asks, tell about ingredients instead.

GENERAL RULES:
- If no product info is available, give simple routine tips, ingredient suggestions, or ask clarifying questions.
- Never include external links.
- Avoid medical claims; stay within gentle skincare guidance.
- Stay supportive, non-judgmental, and user-first at all times.

Your mission: make skincare feel easy, comforting, and doable for the user.
"""

import json

def build_context_messages(user_profile: Dict[str, Any], profile: Dict[str, Any], summary: str, recent: List[Dict[str, str]]):
    msgs: List[Dict[str, str]] = []
    msgs.append({"role": "system", "content": SYSTEM_PROMPT})
    
    up = user_profile or {}
    
    user_profile_str = json.dumps(up)

    p = profile or {}
    prof_lines = []
    # if p.get("name"): prof_lines.append(f"Name: {p.get('name')}")
    # if p.get("skin_type"): prof_lines.append(f"Skin type: {p.get('skin_type')}")
    # if p.get("concerns"): prof_lines.append(f"Concerns: {', '.join(p.get('concerns'))}")
    # if p.get("budget_max") is not None: prof_lines.append(f"Budget max: ₹{p.get('budget_max')}")
    # if p.get("allergies"): prof_lines.append(f"Allergies: {', '.join(p.get('allergies'))}")
    # if p.get("avoid_ingredients"): prof_lines.append(f"Avoid: {', '.join(p.get('avoid_ingredients'))}")
    # if p.get("prefer_ingredients"): prof_lines.append(f"Prefer: {', '.join(p.get('prefer_ingredients'))}")
    # if p.get("fragrance_free") is not None: prof_lines.append(f"Fragrance-free: {p.get('fragrance_free')}")

    # if prof_lines:
    #     msgs.append({"role": "system", "content": "USER PROFILE:\n" + "\n".join(prof_lines)})
    
    msgs.append({"role": "system", "content": "USER DETAILED PROFILE:\n" + user_profile_str})
        
    if summary:
        msgs.append({"role": "system", "content": "CONVERSATION SUMMARY:\n" + summary})

    msgs.extend(recent)
    return msgs

def llm_reply(messages: List[Dict[str, str]], products, intent_recommend: bool) -> str:
    if intent_recommend and products:
        lines = []
        for p in products[:3]:
            md = p.get("metadata", {})
            name = md.get("name", "Unknown")
            price = md.get("price", "?")
            category = md.get("category", "")
            url = md.get("url", "")
            if url and url.startswith("/"):
                url_text = f"URL: {url}"
            else:
                url_text = ""
            ingreds = (md.get("clean_ingreds", "") or "")
            ingreds_short = ingreds[:120] + ("…" if len(ingreds) > 120 else "")
            lines.append(f"- {name} (₹{price}) | {category} | {ingreds_short} {url_text}".strip())
        context_products = "\n".join(lines)
    else:
        context_products = "NO_PRODUCTS"

    messages = messages + [{"role": "system", "content": context_products}]

    if not _groq:
        raise RuntimeError("GROQ_API_KEY not set")

    res = _groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=280
    )
    return res.choices[0].message.content.strip()

from z_chatbot_module.db import db
from bson import ObjectId

async def set_conversation_title(state: Dict[str, Any]) -> Dict[str, Any]:
    uid = state["uid"]
    cid = state["conversation_id"]
    recent = state.get("recent_messages", [])
    
    TITLE_PROMPT = """You are an assistant that creates short conversation titles.
Given the following conversation messages, generate a very short and clear title (1–5 words) that captures the main topic.

Rules:
- Keep it concise (max 5 words)
- No full sentences
- No punctuation
- No quotes
- No disclaimers
- Use title case
- Must describe the topic, not repeat message text verbatim

Return ONLY the title.
"""

    msg_list = [{"role": "system", "content": TITLE_PROMPT}]
    
    msg_list.extend(recent)
    
    title_gen = _groq.chat.completions.create(
        model= GROQ_MODEL,
        messages=msg_list,
        temperature=0.3,
        max_tokens=20
    )    
    
    generated_title = title_gen.choices[0].message.content.strip()
    
    cdb = await db()
    
    await cdb.conversations.update_one({"_id": ObjectId(cid), "uid": uid}, {"$set": {"title": generated_title}})
    
    return {}

async def call_groq_model(prompt: str) -> str:
    if not GROQ_API_KEY :
        return (
            f"[Sample Text] Based on your answers ({prompt[:100]}...), "
            "you should follow a simple daily routine."
        )
    
    system_prompt = """
    You're an skincare expert. 
    Analyze the users skin features based on their answers and give a friendly description in points only. 5 points is enough. start with number. don't say anything extra. just give the 3 line descriptive points.
    And you should response like you're telling to the user about thier skin in a friendly way.
    """
    
    
    response = _groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()
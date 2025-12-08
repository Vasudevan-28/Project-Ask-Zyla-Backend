from __future__ import annotations
import os, textwrap, time
from typing import Dict, Any, List
from bson import ObjectId
from z_chatbot_module.db import db, now_ts
# from z_chatbot_module.auth import AUTH_MODE
from groq import Groq

# SUMMARY_EVERY_TURNS = int(os.getenv("SUMMARY_EVERY_TURNS", "6"))
# SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "1200"))
SUMMARY_EVERY_TURNS = 2
SUMMARY_MAX_CHARS = 1200

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

print(GROQ_API_KEY)
print(GROQ_MODEL)

SUMMARY_INSTRUCTIONS = """Summarize the following chat into 5–8 crisp bullet points capturing:
- user identity tidbits (name, age if given), skin type, budget, allergies, preferences
- key goals and decisions made
- unresolved questions
- strict do/don't preferences.
 Don't leave important keywords
Keep it under 1200 characters. No product hallucinations. Return plain text bullets.
"""

async def get_summary(uid: str, conversation_id: str) -> str:
    d = await db()
    doc = await d.summaries.find_one({"uid": uid, "conversation_id": ObjectId(conversation_id)})
    return doc.get("summary", "") if doc else ""

async def set_summary(uid: str, conversation_id: str, summary: str, turns: int):
    d = await db()
    now = await now_ts()
    await d.summaries.update_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)},
        {"$set": {"summary": summary[:SUMMARY_MAX_CHARS], "turns": turns, "updated_at": now},
         "$setOnInsert": {"uid": uid, "conversation_id": ObjectId(conversation_id), "created_at": now}},
        upsert=True
    )

async def summarize_if_needed(uid: str, conversation_id: str, all_messages: List[Dict[str, str]]) -> str:

    d = await db()
    doc = await d.summaries.find_one({"uid": uid, "conversation_id": ObjectId(conversation_id)})
    turns = int(doc.get("turns", 0)) if doc else 0

    user_turns = sum(1 for m in all_messages if m["role"] == "user")
    if user_turns < 1:
        return doc.get("summary", "") if doc else ""

    do_summarize = (user_turns % SUMMARY_EVERY_TURNS == 0) or (not doc)
    if not do_summarize:
        return doc.get("summary", "") if doc else ""

    text = ""
    for m in all_messages[-(SUMMARY_EVERY_TURNS*2):]:  
        text += f"{m['role'].upper()}: {m['content']}\n"

    if _groq:
        prompt = f"{SUMMARY_INSTRUCTIONS}\n\n{text}"
        res = _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        summary = res.choices[0].message.content.strip()
    else:
        summary = textwrap.shorten(text.replace("\n", " "), width=SUMMARY_MAX_CHARS, placeholder=" …")

    await set_summary(uid, conversation_id, summary, user_turns)
    return summary

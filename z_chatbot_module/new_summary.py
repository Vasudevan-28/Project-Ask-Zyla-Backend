from __future__ import annotations

import os
import textwrap
import json
from typing import Dict, Any, List

from bson import ObjectId

from z_chatbot_module.db import db, now_ts
# from z_chatbot_module.auth import AUTH_MODE 
from groq import Groq

# SUMMARY_EVERY_TURNS = int(os.getenv("SUMMARY_EVERY_TURNS", "8"))
# SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "1200"))
SUMMARY_EVERY_TURNS = 8
SUMMARY_MAX_CHARS = 1200

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL") 

_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

CONVERSATION_SUMMARY_INSTRUCTIONS = """You are updating a running summary of a skincare chat.

Your job:
- Merge the PREVIOUS SUMMARY with NEW MESSAGES.
- Keep only important skincare-relevant information:
  - user identity tidbits (if given): name, age
  - skin type, main concerns, budget level
  - allergies / sensitivities / forbidden ingredients
  - stable preferences (fragrance-free, vegan, etc.)
  - key decisions and recommendations already given
  - unresolved questions or next steps
- Remove outdated or contradicted info (e.g., if skin type changed).
- Keep it compact, 5–8 crisp bullet points max.
- Stay under 1200 characters.
- Do NOT invent new products. Only mention products if the user or assistant already mentioned them.

Return plain text bullet points (no JSON).
"""

USER_PROFILE_EXTRACTION_INSTRUCTIONS = """You are updating a JSON skincare user profile.

Existing profile (may be empty or partial) is below.
You will update it using the conversation summary.
If the summary contradicts the existing profile, prefer the most recent info in the summary.

VALID VALUES / FIELDS:
- skin_type: one of "oily", "dry", "combination", "sensitive", "normal", "unknown"
- concerns: array of short strings, like ["acne", "hyperpigmentation"]
- sensitivities: array of ingredients or properties the user reacts badly to,
  e.g. ["fragrance", "benzoyl peroxide"]
- preferences: array of short strings like ["fragrance-free", "non-comedogenic", "vegan"]
- budget_level: one of "low", "medium", "high", "unknown"
- max_price_per_product: number or null if not given
- current_routine: object with optional "morning" and "night" arrays of short product/step strings
- notes: short free-text string with any other relevant long-term info.

Rules:
- Only use information that clearly appears in the conversation summary.
- Use "unknown", null, or empty arrays when the data is not known.
- If user changed their mind (e.g. oily -> combination), keep only the latest.
- Do NOT hallucinate brands or products.

Return ONLY valid JSON, no extra text.
"""


async def get_summary(uid: str, conversation_id: str) -> str:
    print("GETTING SUMMARY")
    d = await db()
    doc = await d.summaries.find_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)}
    )
    return doc.get("summary", "") if doc else ""


async def set_summary(uid: str, conversation_id: str, summary: str, user_turns: int):
    print("SETTING SUMMARY")
    d = await db()
    now = await now_ts()
    await d.summaries.update_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)},
        {
            "$set": {
                "summary": summary[:SUMMARY_MAX_CHARS],
                "turns": user_turns,
                "updated_at": now,
            },
            "$setOnInsert": {
                "uid": uid,
                "conversation_id": ObjectId(conversation_id),
                "created_at": now,
            },
        },
        upsert=True,
    )


async def summarize_conversation_if_needed(
    uid: str,
    conversation_id: str,
    all_messages: List[Dict[str, str]],
) -> str:

    d = await db()
    doc = await d.summaries.find_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)}
    )

    previous_summary = doc.get("summary", "") if doc else ""
    previous_user_turns = int(doc.get("turns", 0)) if doc else 0

    total_user_turns = 0
    new_messages: List[Dict[str, str]] = []

    for m in all_messages:
        if m.get("role") == "user":
            total_user_turns += 1
        if total_user_turns > previous_user_turns:
            new_messages.append(m)

    if total_user_turns < 1:
        return previous_summary

    new_user_turns = total_user_turns - previous_user_turns
    do_summarize = (doc is None) or (new_user_turns >= SUMMARY_EVERY_TURNS)

    if (not do_summarize) or (not new_messages):
        return previous_summary

    new_text_lines: List[str] = []
    for m in new_messages:
        role = (m.get("role") or "").upper()
        content = m.get("content") or ""
        new_text_lines.append(f"{role}: {content}")
    new_text_block = "\n".join(new_text_lines)

    if _groq and GROQ_MODEL:
        prompt = (
            f"{CONVERSATION_SUMMARY_INSTRUCTIONS}\n\n"
            f"PREVIOUS SUMMARY:\n{previous_summary or '(none yet)'}\n\n"
            f"NEW MESSAGES (most recent last):\n{new_text_block}\n"
        )

        res = _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        updated_summary = (res.choices[0].message.content or "").strip()
    else:
        combined = (previous_summary + "\n" + new_text_block).strip()
        updated_summary = textwrap.shorten(
            combined.replace("\n", " "),
            width=SUMMARY_MAX_CHARS,
            placeholder=" …",
        )

    await set_summary(uid, conversation_id, updated_summary, total_user_turns)
    # await update_user_profile_from_summary(uid, updated_summary)
    return updated_summary



# async def get_user_profile(uid: str) -> Dict[str, Any]: 
#     d = await db()
#     doc = await d.user_profiles.find_one({"uid": uid})
#     return doc.get("profile", {}) if doc else {}

async def get_user_profile(uid: str) -> Dict[str, Any]: 
    d = await db()
    doc = await d.user_profiles.find_one({"uid": uid})
    return doc.get("profile", {}) if doc else {}

async def get_user_skin_profile(uid: str) -> Dict[str, Any]: 
    d = await db()
    doc = await d.skinData.find_one({"skinProfileData.userId": uid}, {"skinProfileData.userId" : 0})
    return doc.get("skinProfileData", {}) if doc else {}


async def set_user_profile(uid: str, profile: Dict[str, Any]) -> None:
    d = await db()
    now = await now_ts()
    await d.user_profiles.update_one(
        {"uid": uid},
        {
            "$set": {"profile": profile, "updated_at": now},
            "$setOnInsert": {"uid": uid, "created_at": now},
        },
        upsert=True,
    )


async def update_user_profile_from_summary(
    uid: str,
    conversation_summary: str,
) -> Dict[str, Any]:

    existing_profile = await get_user_profile(uid)

    if not conversation_summary:
        return existing_profile

    if not (_groq and GROQ_MODEL):
        return existing_profile

    prompt = (
        f"{USER_PROFILE_EXTRACTION_INSTRUCTIONS}\n\n"
        f"EXISTING PROFILE JSON:\n"
        f"{json.dumps(existing_profile, ensure_ascii=False, indent=2)}\n\n"
        f"CONVERSATION SUMMARY:\n{conversation_summary}\n"
    )

    res = _groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500,
    )
    raw = (res.choices[0].message.content or "").strip()

    try:
        new_profile = json.loads(raw)
        if not isinstance(new_profile, dict):
            raise ValueError("Profile is not a JSON object.")
    except Exception:
        return existing_profile

    await set_user_profile(uid, new_profile)
    return new_profile

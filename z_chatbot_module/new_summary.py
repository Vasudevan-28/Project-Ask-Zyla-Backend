from __future__ import annotations

import os
import textwrap
import json
from typing import Dict, Any, List

from bson import ObjectId

from utils.db import get_db, now_ts
# from z_chatbot_module.auth import AUTH_MODE 
from groq import Groq

# SUMMARY_EVERY_TURNS = int(os.getenv("SUMMARY_EVERY_TURNS", "8"))
# SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "1200"))
SUMMARY_EVERY_TURNS = 8
SUMMARY_MAX_CHARS = 1200

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL") 

_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

CONVERSATION_SUMMARY_INSTRUCTIONS = """
You are maintaining a concise, cumulative summary of an ongoing skincare conversation.

Your task:
- Merge the PREVIOUS SUMMARY with the NEW MESSAGES.
- Preserve only durable, skincare-relevant information that should carry forward across turns.

Always prioritize:
- Primary and secondary skin concerns
- Skin type (only the most current assessment)
- Allergies, sensitivities, and explicitly forbidden ingredients
- Stable preferences (e.g., fragrance-free, vegan, budget limits)
- Confirmed recommendations or routines already agreed upon
- Open questions, pending tests, or next steps

Rules:
- Remove or replace outdated, corrected, or contradicted information.
- Do not repeat temporary symptoms unless they persist across messages.
- Do NOT invent products, diagnoses, or ingredients.
- Mention products or brands only if explicitly stated by the user or assistant.
- Keep language factual, neutral, and non-speculative.

Output format:
- Plain-text bullet points only (no JSON, no headings).
- 5–8 bullets maximum.
- Total length under 1200 characters.
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
    d = get_db()
    doc = await d.summaries.find_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)}
    )
    return doc.get("summary", "") if doc else ""


async def set_summary(uid: str, conversation_id: str, summary: str, user_turns: int):
    print("SETTING SUMMARY")
    d = get_db()
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


# async def summarize_conversation_if_needed(
#     uid: str,
#     conversation_id: str,
#     all_messages: List[Dict[str, str]],
#     turns : int
# ) -> str:

#     d = get_db()
#     doc = await d.summaries.find_one(
#         {"uid": uid, "conversation_id": ObjectId(conversation_id)}
#     )

#     previous_summary = doc.get("summary", "") if doc else ""
#     previous_user_turns = int(doc.get("turns", 0)) if doc else 0

#     total_user_turns = 0
#     new_messages: List[Dict[str, str]] = []

#     for m in all_messages:
#         if m.get("role") == "user":
#             total_user_turns += 1
#         if total_user_turns > previous_user_turns:
#             new_messages.append(m)

#     if total_user_turns < 1:
#         return previous_summary

#     new_user_turns = total_user_turns - previous_user_turns
#     do_summarize = (doc is None) or (new_user_turns >= 8)

#     if (not do_summarize) or (not new_messages):
#         return previous_summary

#     new_text_lines: List[str] = []
#     for m in new_messages:
#         role = (m.get("role") or "").upper()
#         content = m.get("content") or ""
#         new_text_lines.append(f"{role}: {content}")
#     new_text_block = "\n".join(new_text_lines)

#     if _groq and GROQ_MODEL:
#         prompt = (
#             f"{CONVERSATION_SUMMARY_INSTRUCTIONS}\n\n"
#             f"PREVIOUS SUMMARY:\n{previous_summary or '(none yet)'}\n\n"
#             f"NEW MESSAGES (most recent last):\n{new_text_block}\n"
#         )

#         res = _groq.chat.completions.create(
#             model=GROQ_MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2,
#             max_tokens=400,
#         )
#         updated_summary = (res.choices[0].message.content or "").strip()
#     else:
#         combined = (previous_summary + "\n" + new_text_block).strip()
#         updated_summary = textwrap.shorten(
#             combined.replace("\n", " "),
#             width=1200,
#             placeholder=" …",
#         )

#     await set_summary(uid, conversation_id, updated_summary, total_user_turns)
#     # await update_user_profile_from_summary(uid, updated_summary)
#     return updated_summary

async def summarize_conversation_if_needed(
    uid: str,
    conversation_id: str,
    all_messages: List[Dict[str, str]],
    turns: int,
) -> str:

    if not all_messages:
        return ""

    d = get_db()
    doc = await d.summaries.find_one(
        {"uid": uid, "conversation_id": ObjectId(conversation_id)}
    )

    previous_summary = doc.get("summary", "") if doc else ""
    previous_user_turns = int(doc.get("turns", 0)) if doc else 0

    # Safety guard: prevent double-summarization
    if turns <= previous_user_turns:
        return previous_summary

    # Build summary input directly from windowed messages
    new_text_lines: List[str] = []
    for m in all_messages:
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
            width=1200,
            placeholder=" …",
        )

    await set_summary(uid, conversation_id, updated_summary, turns)
    return updated_summary


# async def get_user_profile(uid: str) -> Dict[str, Any]: 
#     d = get_db()
#     doc = await d.user_profiles.find_one({"uid": uid})
#     return doc.get("profile", {}) if doc else {}


async def get_user_skin_profile(uid: str) -> Dict[str, Any]: 
    d = get_db()
    doc = await d.skinData.find_one(
    {"skinProfileData.userId": uid},
    {
        "_id": 0,
        "skinProfileData.userId": 0,
        "skinProfileData.zyla_summary": 0
    }
    )
    return doc.get("skinProfileData", {}) if doc else {}


# async def set_user_profile(uid: str, profile: Dict[str, Any]) -> None:
#     d = get_db()
#     now = await now_ts()
#     await d.user_profiles.update_one(
#         {"uid": uid},
#         {
#             "$set": {"profile": profile, "updated_at": now},
#             "$setOnInsert": {"uid": uid, "created_at": now},
#         },
#         upsert=True,
#     )


# async def update_user_profile_from_summary(
#     uid: str,
#     conversation_summary: str,
# ) -> Dict[str, Any]:

#     existing_profile = await get_user_skin_profile(uid)

#     if not conversation_summary:
#         return existing_profile

#     if not (_groq and GROQ_MODEL):
#         return existing_profile

#     prompt = (
#         f"{USER_PROFILE_EXTRACTION_INSTRUCTIONS}\n\n"
#         f"EXISTING PROFILE JSON:\n"
#         f"{json.dumps(existing_profile, ensure_ascii=False, indent=2)}\n\n"
#         f"CONVERSATION SUMMARY:\n{conversation_summary}\n"
#     )

#     res = _groq.chat.completions.create(
#         model=GROQ_MODEL,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.0,
#         max_tokens=500,
#     )
#     raw = (res.choices[0].message.content or "").strip()

#     try:
#         new_profile = json.loads(raw)
#         if not isinstance(new_profile, dict):
#             raise ValueError("Profile is not a JSON object.")
#     except Exception:
#         return existing_profile

#     await set_user_profile(uid, new_profile)
#     return new_profile

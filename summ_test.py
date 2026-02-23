# from utils.db import get_db
# from typing import Dict, Any, List
# from bson import ObjectId

# def get_messages_for_summary_window():
    
#     uid = "AGpellMeSGfg6bGcP2F0S1ojDGU2"
 
#     conversation_id = ("6963d377004990b4079d66b0"), 
    
#     if 8 <= 0 or 8 % 8 != 0:
#         return []

#     d = get_db()

#     ok = d.conversations.find_one(
#         {"_id": ObjectId(conversation_id), "uid": uid}
#     )

#     if not ok:
#         return []

#     start_user_turn = 8 - 8
#     end_user_turn = 8

#     cur = (
#         d.messages
#         .find({"conversation_id": ObjectId(conversation_id), "uid": uid})
#         .sort("created_at", 1)
#     )

#     out: List[Dict[str, Any]] = []
#     user_turn_count = 0
#     collecting = False

#     for m in cur:
#         role = m.get("role")

#         if role == "user":
#             user_turn_count += 1

#             if user_turn_count == start_user_turn + 1:
#                 collecting = True

#             if user_turn_count > end_user_turn:
#                 break

#         if collecting:
#             out.append({
#                 "id": str(m["_id"]),
#                 "role": role,
#                 "content": m.get("content"),
#                 "created_at": m.get("created_at"),
#             })

#     print(out)



# get_messages_for_summary_window()



from utils.db import get_db
from typing import Dict, Any, List
from bson import ObjectId


async def get_messages_for_summary_window():
    uid = "AGpellMeSGfg6bGcP2F0S1ojDGU2"
    conversation_id = "6963d377004990b4079d66b0"

    if 8 <= 0 or 8 % 8 != 0:
        return []

    d = get_db()

    ok = await d.conversations.find_one(
        {"_id": ObjectId(conversation_id), "uid": uid}
    )
    if not ok:
        return []

    start_user_turn = 8 - 8
    end_user_turn = 8

    cur = (
        d.messages
        .find({"conversation_id": ObjectId(conversation_id), "uid": uid})
        .sort("created_at", 1)
    )

    out: List[Dict[str, Any]] = []
    user_turn_count = 0
    collecting = False

    async for m in cur:
        role = m.get("role")

        if role == "user":
            user_turn_count += 1

            if user_turn_count == start_user_turn + 1:
                collecting = True

            if user_turn_count > end_user_turn:
                break

        if collecting:
            out.append({
                "id": str(m["_id"]),
                "role": role,
                "content": m.get("content"),
                "created_at": m.get("created_at"),
            })

    print(out)


import asyncio

if __name__ == "__main__":
    asyncio.run(get_messages_for_summary_window())






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

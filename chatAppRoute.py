from __future__ import annotations
from fastapi import APIRouter
from z_chatbot_module.conversations import conversation_router
from z_chatbot_module.chatbot import chatbot_router

# app = FastAPI(title="Ask Zyla Auth", version="1.0.0")

chatApp = APIRouter(prefix="/chatApp", tags=["chat app"])

chatApp.include_router(conversation_router)

chatApp.include_router(chatbot_router)

# chatApp.include_router(appAuth)

@chatApp.get("/testChatApp")
def testingApi():
    return {"ChatApp": "Connected"}

    



# chat_app = build_chat_graph()

# @chatApp.post("/chatgraph", response_model=ChatResponse)
# async def chat(req: ChatRequest, user=Depends(auth_user_fb)):
#     uid = user["uid"]

#     initial_state = {
#         "uid": uid,
#         "conversation_id": req.conversation_id,
#         "message": req.message,
#     }

#     final_state = await chat_app.ainvoke(initial_state)

#     return ChatResponse(
#         conversation_id=final_state["conversation_id"],
#         reply=final_state["reply"],
#         # intent_query = final_state["intent_query"],
#         # hits=final_state.get("hits", []),
#         # intent_recommend=bool(final_state.get("intent_recommend", False)),
#         used_messages=final_state.get("used_messages", []),
#         # profile_used=Profile(**final_state.get("profile", {})),
#         user_profile=final_state["user_profile"],
#         summary=final_state.get("summary", "") or "",
#     )
    
# from z_chatbot_module.guest_session import TrialSession, get_trial_session
# from z_chatbot_module.chat_graph import build_trial_chat_graph
# from z_chatbot_module.schemas import TrialUserChkResponse

# trialChat = build_trial_chat_graph()

# @chatApp.post("/trial/chat/trialUser")
# async def trial_chk(session: TrialSession = Depends(get_trial_session), response: Response = None):
#     if session.remaining_trials <= 0:
#         raise HTTPException(
#             status_code = 402,
#             detail={
#               "code": "TRIAL_EXHAUSTED",
#                 "message": "Your free trial is over. Please sign up to continue chatting.",   
#             }
#         )
        
#     new_chat_count = session.chat_count
#     new_remaining = max(0, 3 - new_chat_count)
#     trial_exhausted = new_remaining == 0

#     if response is not None:
#         response.set_cookie(
#             key="trial_id",
#             value=session.guest_id,
#             max_age=60 * 60 * 24 * 7, 
#             httponly=True,
#             samesite="lax",
#         )

#     uid = f"guest:{session.guest_id}"

    
#     return TrialUserChkResponse(
#         guest_id=uid,
#         remaining_trials=new_remaining,
#         trials_exhausted=trial_exhausted
        
#     )

# @chatApp.post("/trial/chat", response_model=TrialChatResponse)
# async def trial_chat(
#     req: TrialChatRequest,
#     session: TrialSession = Depends(get_trial_session),
#     response: Response = None,
# ):
#     d = get_db()

#     if session.remaining_trials <= 0:
#         raise HTTPException(
#             status_code=402,
#             detail={
#                 "code": "TRIAL_EXHAUSTED",
#                 "message": "Your free trial is over. Please sign up to continue chatting.",
#             },
#         )

#     new_chat_count = session.chat_count + 1
#     new_remaining = max(0, 3 - new_chat_count)

#     await d.guest_sessions.update_one(
#         {"_id": ObjectId(session.guest_id)},
#         {
#             "$set": {
#                 "chat_count": new_chat_count,
#                 "updated_at": await now_ts(),
#             }
#         },
#     )

#     if response is not None:
#         response.set_cookie(
#             key="trial_id",
#             value=session.guest_id,
#             max_age=60 * 60 * 24 * 7, 
#             httponly=True,
#             secure=True,
#             samesite="none",
#         )

#     uid = f"guest:{session.guest_id}"

#     initial_state = {
#         "guest_id": uid,
#         "conversation_id": req.conversation_id,
#         "message": req.message,
#     }

#     final_state = await trialChat.ainvoke(initial_state)

#     trial_exhausted = new_remaining == 0

#     return TrialChatResponse(
#         conversation_id=final_state["conversation_id"],
#         reply=final_state["reply"],
#         remaining_trials=new_remaining,
#         trials_exhausted=trial_exhausted,
#     )

    
    


# @chatApp.get("/skin-profile/{user_id}")
# async def get_skin_profile(user_id: str):
    
#     spdb = get_db()
    
#     # doc = await spdb.skinData.find_one({"skinProfileData.userId": user_id})
#     doc = await spdb.skinData.find_one({"userId": user_id})
#     if not doc:
#         raise HTTPException(status_code=404, detail="Profile not found")
    
#     # cleared = doc.get("cleared", False)
    
#     # if cleared:
#     #     raise HTTPException(status_code=404, detail="data is cleared")     

#     doc["_id"] = str(doc["_id"])
#     return doc


# from datetime import datetime

# @chatApp.put("/skin-answers-add/{user_id}")
# async def add_skin_answers(user_id: str, data: SkinProfileWrapper):
#     spdb = get_db()

#     body = data.skinProfileData.model_dump()

#     user = await spdb.users.find_one(
#         {"firebase_uid": user_id},
#         {"name": 1, "dob": 1, "gender": 1}  
#     )

#     if not user:
#         return {"error": "User not found"}

#     def calculate_age(dob_str):
#         dob = datetime.strptime(dob_str, "%Y-%m-%d")
#         today = datetime.today()
#         return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

#     age = calculate_age(user["dob"])

#     body["userId"] = user_id
#     body["name"] = user["name"]
#     body["gender"] = user["gender"]
#     body["age"] = age  

#     # existing = await spdb.skinData.find_one({"skinProfileData.userId": user_id})
#     existing = await spdb.skinData.find_one({"userId": user_id})

#     if not existing:
#         await spdb.skinData.insert_one({"skinProfileData": body, "userId" : user_id, "cleared" : False})
#         await spdb.users.update_one({"firebase_uid" : user_id},
#                                 {"$set": {"skin_profile" : True}})
#         return {"message": "Skin profile created successfully"}

#     # result = await spdb.skinData.update_one(
#     #     {"skinProfileData.userId": user_id},
#     #     {"$set": {"skinProfileData": body}}
#     # )
#     result = await spdb.skinData.update_one(
#         {"userId": user_id},
#         {"$set": {"skinProfileData": body, "userId" : user_id, "cleared" : False}}
#     )
    
#     await spdb.users.update_one({"firebase_uid" : user_id},
#                                 {"$set": {"skin_profile" : True}})

#     if result.modified_count == 0:
#         return {"message": "No changes made, profile already up to date"}

#     return {"message": "Skin profile updated successfully"}




# import json

# from z_chatbot_module.llm_core import call_groq_model

# def calculate_age(dob_str: str) -> int:
#     dob = datetime.strptime(dob_str, "%Y-%m-%d")
#     today = datetime.today()
#     return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# @chatApp.put("/skin-profile/{user_id}")
# async def update_skin_profile(user_id: str, data: SkinProfileWrapper):
#     spdb = get_db()

#     user = await spdb.users.find_one(
#         {"firebase_uid": user_id},
#         {"name": 1, "dob": 1, "gender": 1}
#     )

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     age = calculate_age(user["dob"])

#     base_data = data.skinProfileData.model_dump()

#     enriched_data = {
#         **base_data,
#         "userId": user_id,
#         "name": user["name"],
#         "gender": user["gender"],
#         "age": age,
#     }

#     prompt = json.dumps(enriched_data)
#     description = await call_groq_model(prompt)

#     updated_data = {
#         **enriched_data,
#         "zyla_summary": description,
#     }

#     await spdb.skinData.update_one(
#         {"skinProfileData.userId": user_id},
#         {"$set": {"skinProfileData": updated_data}},
#         upsert=True,
#     )

#     saved_doc = await spdb.skinData.find_one(
#         {"skinProfileData.userId": user_id},
#         {"_id": 0}
#     )

#     return saved_doc



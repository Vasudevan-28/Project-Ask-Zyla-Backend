from fastapi import APIRouter, HTTPException, Depends
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from z_skinprofile.sp_schemas import SkinProfileWrapper
import json

from z_chatbot_module.llm_core import call_groq_model
from datetime import datetime


skinpro_router = APIRouter(prefix="/skinprofile")



def calculate_age(dob_str: str) -> int:
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# @skinpro_router.get("/skin-profile/{user_id}")
# async def get_skin_profile(user_id: str):
@skinpro_router.get("/skin-profile")
async def get_skin_profile( user = Depends(auth_user_fb) ):
    user_id = user["uid"]
    spdb = get_db()
    
    # doc = await spdb.skinData.find_one({"skinProfileData.userId": user_id})
    doc = await spdb.skinData.find_one({"userId": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")  

    doc["_id"] = str(doc["_id"])
    return doc


@skinpro_router.put("/skin-answers-add")
async def add_skin_answers(data: SkinProfileWrapper, user = Depends(auth_user_fb)):
    spdb = get_db()

    user_id = user["uid"]  

    body = data.skinProfileData.model_dump()

    user_doc = await spdb.users.find_one(
        {"firebase_uid": user_id},
        {"name": 1, "dob": 1, "gender": 1}
    )

    if not user_doc:
        return {"error": "User not found"}

    age = calculate_age(user_doc["dob"])

    # body["userId"] = user_id
    body["name"] = user_doc["name"]
    body["gender"] = user_doc["gender"]
    body["age"] = age

    existing = await spdb.skinData.find_one({"userId": user_id})

    if not existing:
        await spdb.skinData.insert_one({
            "skinProfileData": body,
            "userId": user_id,
            "cleared": False
        })

        await spdb.users.update_one(
            {"firebase_uid": user_id},
            {"$set": {"skin_profile": True, "registered" : True}}
        )

        return {"message": "Skin profile created successfully"}

    result = await spdb.skinData.update_one(
        {"userId": user_id},
        {"$set": {
            "skinProfileData": body,
            "cleared": False
        }}
    )

    await spdb.users.update_one(
        {"firebase_uid": user_id},
        {"$set": {"skin_profile": True}}
    )

    if result.modified_count == 0:
        return {"message": "No changes made, profile already up to date"}

    return {"message": "Skin profile updated successfully"}





# @skinpro_router.put("/skin-profile/{user_id}")
@skinpro_router.put("/skin-profile")
async def update_skin_profile(data: SkinProfileWrapper, user = Depends(auth_user_fb)):
    user_id = user["uid"]
    
    spdb = get_db()

    user = await spdb.users.find_one(
        {"firebase_uid": user_id},
        {"name": 1, "dob": 1, "gender": 1}
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    age = calculate_age(user["dob"])

    base_data = data.skinProfileData.model_dump()

    enriched_data = {
        **base_data,
        "userId": user_id,
        "name": user["name"],
        "gender": user["gender"],
        "age": age,
    }

    prompt = json.dumps(enriched_data)
    description = await call_groq_model(prompt)

    updated_data = {
        **enriched_data,
        "zyla_summary": description,
    }

    await spdb.skinData.update_one(
        # {"skinProfileData.userId": user_id},
        {"userId": user_id},
        {"$set": {"skinProfileData": updated_data}},
        upsert=True,
    )

    saved_doc = await spdb.skinData.find_one(
        # {"skinProfileData.userId": user_id},
        {"userId": user_id},
        {"_id": 0}
    )

    return saved_doc



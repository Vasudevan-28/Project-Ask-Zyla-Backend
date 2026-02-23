import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from z_settings.sett_models import ProfileUpdate, FeedbackUpdate, RatingUpdate, SupportUpdate, GenSupport, FeedbackSubmit

from utils._auth_firebase import auth_user_fb
from utils.db import get_db
from datetime import datetime

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zyla-backend")

sett = APIRouter(prefix="/settings")

# MODELS

# class ProfileModel(BaseModel):
#     name: str
#     age: int
#     email: EmailStr
#     phone_number: str
#     gender: str
#     address: Dict[str, Any] = Field(default_factory=dict)


# HELPERS

def serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    _id = d.pop("_id", None)
    if _id is not None:
        d["id"] = str(_id)
    return d

# --- User-specific Data Helpers ---

async def get_or_create_profile(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    
    spdb = get_db()
    
    try:
        doc = await spdb.users.find_one({"firebase_uid": uid})  # type: ignore
    except PyMongoError as e:
        logger.error(f"profile find_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    if doc:
        return doc

    default_profile = {
        "firebase_uid": uid,
        "name": "User",
        "age": 22,
        "email": "user@mail.com",
        "phone_number": "9876543210",
        "gender": "Male",
        "address": {
            "flat_or_house": "12B",
            "street": "MG Road",
            "city_or_Village": "Vellore",
            "district": "Vellore",
            "state": "Tamil Nadu",
            "country": "India",
        },
    }
    try:
        result = await spdb.users.insert_one(default_profile)  # type: ignore
    except PyMongoError as e:
        logger.error(f"profile insert_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    default_profile["_id"] = result.inserted_id
    return default_profile

async def get_or_create_feedback(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    spdb = get_db()
    try:
        doc = await spdb.feedback_col.find_one({"firebase_uid": uid})  
    except PyMongoError as e:
        logger.error(f"feedback find_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    if doc:
        return doc
    default_doc = {"firebase_uid": uid, "feedback": ""}
    try:
        result = await spdb.feedback_col.insert_one(default_doc)  
    except PyMongoError as e:
        logger.error(f"feedback insert_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    default_doc["_id"] = result.inserted_id
    return default_doc

async def get_or_create_rating(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    spdb = get_db()
    try:
        doc = await spdb.rating_col.find_one({"firebase_uid": uid})  
    except PyMongoError as e:
        logger.error(f"rating find_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    if doc:
        return doc
    default_doc = {"firebase_uid": uid, "rating": None}
    try:
        result = await spdb.rating_col.insert_one(default_doc)  # type: ignore
    except PyMongoError as e:
        logger.error(f"rating insert_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    default_doc["_id"] = result.inserted_id
    return default_doc

async def get_or_create_support(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    spdb = get_db()
    try:
        doc = support_col.find_one({"firebase_uid": uid})  # type: ignore
    except PyMongoError as e:
        logger.error(f"support find_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    if doc:
        return doc
    default_doc = {"firebase_uid": uid, "message": ""}
    try:
        result = await spdb.support_col.insert_one(default_doc)  # type: ignore
    except PyMongoError as e:
        logger.error(f"support insert_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    default_doc["_id"] = result.inserted_id
    return default_doc


# -------- PROFILE --------

@sett.get("/profile")
async def get_profile(user: dict = Depends(auth_user_fb)):
# async def get_profile():
    # doc = await get_or_create_profile("helloo")
    doc = await get_or_create_profile(user["uid"])
    return serialize(doc)

@sett.put("/profile")
async def update_profile(payload: ProfileUpdate, user: dict = Depends(auth_user_fb)):
    spdb = get_db()
    doc = await get_or_create_profile(user["uid"])
    user_id = doc["_id"]

    update_fields: Dict[str, Any] = {}
    if payload.name is not None:
        update_fields["name"] = payload.name
    if payload.dob is not None:
        update_fields["dob"] = payload.dob
    if payload.gender is not None:
        update_fields["gender"] = payload.gender
    if payload.city is not None:
        update_fields["city"] = payload.city
    if payload.state is not None:
        update_fields["state"] = payload.state

    if not update_fields:
        return {
            "detail": "Nothing to update",
            "profile": serialize(doc),
        }
    try:
        await spdb.users.update_one({"_id": user_id}, {"$set": update_fields})
        updated = await spdb.users.find_one({"_id": user_id})
    except PyMongoError as e:
        logger.error(f"profile update/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    return {
        "message": "Profile updated successfully",
        "profile": serialize(updated),
    }

# -------- FEEDBACK --------

@sett.get("/feedback")
async def get_feedback(user: dict = Depends(auth_user_fb)):
    doc = get_or_create_feedback(user["uid"])
    return serialize(doc)

@sett.put("/feedback")

async def update_feedback(payload: FeedbackUpdate, user: dict = Depends(auth_user_fb)):
    spdb = get_db()

    doc = {
        "uid": user["uid"],
        "feedback": payload.feedback,
        "name": payload.name,
        "created_at": datetime.utcnow(),  
    }

    try:
        result = await spdb.feedback_col.insert_one(doc)
        inserted = await spdb.feedback_col.find_one({"_id": result.inserted_id})

    except PyMongoError as e:
        logger.error(f"feedback insert/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")

    return {
        "message": "Feedback saved",
        "feedback": serialize(inserted),
    }

# -------- RATING --------

@sett.get("/rating")
async def get_rating(user: dict = Depends(auth_user_fb)):
    doc = get_or_create_rating(user["uid"])
    return serialize(doc)

@sett.put("/rating")
async def update_rating(payload: RatingUpdate, user: dict = Depends(auth_user_fb)):
    spdb = get_db()

    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="rating must be 1–5")

    doc = {
        "uid": user["uid"],
        "rating": payload.rating,
        "created_at": datetime.utcnow(), 
    }

    try:
        result = await spdb.rating_col.insert_one(doc)
        inserted = await spdb.rating_col.find_one({"_id": result.inserted_id})

    except PyMongoError as e:
        logger.error(f"rating insert/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")

    return {
        "message": "Rating saved",
        "rating": serialize(inserted),
    }


# -------- SUPPORT --------

@sett.get("/support")
async def get_support(user: dict = Depends(auth_user_fb)):
    doc = get_or_create_support(user["uid"])
    return serialize(doc)



@sett.put("/support")
async def update_support(payload: SupportUpdate, user: dict = Depends(auth_user_fb)):
    spdb = get_db()

    doc = {
        "uid": user["uid"],
        "message": payload.message,
        "created_at": datetime.utcnow(),  
    }

    try:
        result = await spdb.support_col.insert_one(doc)

        inserted = await spdb.support_col.find_one({"_id": result.inserted_id})

    except PyMongoError as e:
        logger.error(f"support insert/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")

    return {
        "message": "Support message saved",
        "support": serialize(inserted),
    }
    
    

@sett.put("/general-support")
async def update_general_support(payload: GenSupport):
    spdb = get_db()

    doc = {
        "name": payload.name,
        "email": payload.email,
        "message": payload.message,
        "created_at": str(datetime.now),
    }

    try:
        result = await spdb.general_support.insert_one(doc)
        inserted = await spdb.general_support.find_one({"_id": result.inserted_id})
    except PyMongoError as e:
        logger.error(f"support insert/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")

    return {
        "message": "Support message saved",
        "support": serialize(inserted),
    }


    
from datetime import datetime

@sett.post('/feedback-submit')
async def submitFeedback(payload : FeedbackSubmit, user : dict = Depends(auth_user_fb)):
    uid = user["uid"]
    spdb = get_db()
    
    doc = {
         "firebase_uid" : uid,
        "feedback" : payload.emotion,
        "feedbackLabel" : payload.emotionLabel,
        "feedback_time" : str(datetime.now())
    }

    
    try:
        result = await spdb.user_feedback.insert_one(doc)
        inserted = await spdb.user_feedback.find_one({"_id": result.inserted_id})
    except PyMongoError as e:
        logger.error(f"feedback insert/find error: {e}")
        raise HTTPException(status_code=503, detail="Database error")

    return {
        "message": "feedback report saved",
        "data": serialize(inserted),
    }
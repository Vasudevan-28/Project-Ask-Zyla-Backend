import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from z_chatbot_module._auth_firebase import auth_user_fb
from z_chatbot_module.db import db
from datetime import datetime

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zyla-backend")

# DB CONFIG
# MONGO_URI = "mongodb+srv://thukk_db:thuk@cluster0.5wsgjtp.mongodb.net/"
# DB_NAME = "sett_samp"

# PROFILE_COLL = "profile"
# FEEDBACK_COLL = "feedback"
# RATING_COLL = "rating"
# SUPPORT_COLL = "support"


# try:
#     client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#     client.admin.command("ping")
#     db = client[DB_NAME]
#     profile_col = db[PROFILE_COLL]
#     feedback_col = db[FEEDBACK_COLL]
#     rating_col = db[RATING_COLL]
#     support_col = db[SUPPORT_COLL]
#     logger.info("Connected to MongoDB OK")
# except Exception as e:
#     logger.error(f"MongoDB connection failed: {e}")
#     client = None
#     profile_col = feedback_col = rating_col = support_col = None

# FASTAPI APP
# sett = FastAPI(title="Ask Zyla – Multi Collection (multi user)")
sett = APIRouter(prefix="/settings")


# sett.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# MODELS

class ProfileModel(BaseModel):
    name: str
    age: int
    email: EmailStr
    phone_number: str
    gender: str
    address: Dict[str, Any] = Field(default_factory=dict)

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None

class FeedbackUpdate(BaseModel):
    name: str
    feedback: str

class RatingUpdate(BaseModel):
    rating: int

class SupportUpdate(BaseModel):
    message: str

# HELPERS

# def ensure_connected():
#     if any(c is None for c in (profile_col, feedback_col, rating_col, support_col)):
#         raise HTTPException(
#             status_code=503,
#             detail="Database unavailable. Check MongoDB connection.",
#         )

def serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    _id = d.pop("_id", None)
    if _id is not None:
        d["id"] = str(_id)
    return d

# --- User-specific Data Helpers ---

async def get_or_create_profile(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    
    spdb = await db()
    
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
    spdb = await db()
    try:
        doc = await spdb.feedback_col.find_one({"firebase_uid": uid})  # type: ignore
    except PyMongoError as e:
        logger.error(f"feedback find_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    if doc:
        return doc
    default_doc = {"firebase_uid": uid, "feedback": ""}
    try:
        result = await spdb.feedback_col.insert_one(default_doc)  # type: ignore
    except PyMongoError as e:
        logger.error(f"feedback insert_one error: {e}")
        raise HTTPException(status_code=503, detail="Database error")
    default_doc["_id"] = result.inserted_id
    return default_doc

async def get_or_create_rating(uid: str) -> Dict[str, Any]:
    # ensure_connected()
    spdb = await db()
    try:
        doc = await spdb.rating_col.find_one({"firebase_uid": uid})  # type: ignore
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
    spdb = await db()
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

# ROUTES

@sett.get("/")
def root():
    return {"message": "API is running"}

# -------- PROFILE --------

@sett.get("/profile")
async def get_profile(user: dict = Depends(auth_user_fb)):
# async def get_profile():
    # doc = await get_or_create_profile("helloo")
    doc = await get_or_create_profile(user["uid"])
    return serialize(doc)

@sett.put("/profile")
async def update_profile(payload: ProfileUpdate, user: dict = Depends(auth_user_fb)):
    spdb = await db()
    doc = await get_or_create_profile(user["uid"])
    user_id = doc["_id"]

    update_fields: Dict[str, Any] = {}
    if payload.name is not None:
        update_fields["name"] = payload.name
    if payload.age is not None:
        update_fields["dob"] = payload.dob
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
    spdb = await db()

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

# async def update_feedback(payload: FeedbackUpdate, user: dict = Depends(auth_user_fb)):
#     spdb = await db()
#     doc = get_or_create_feedback(user["uid"])
#     doc_id = doc["_id"]
#     try:
#         await spdb.feedback_col.update_one(
#             {"_id": doc_id}, {"$set": {"feedback": payload.feedback}}
#         )
#         updated = await spdb.feedback_col.find_one({"_id": doc_id})
#     except PyMongoError as e:
#         logger.error(f"feedback update/find error: {e}")
#         raise HTTPException(status_code=503, detail="Database error")
#     return {"message": "Feedback updated", "feedback": serialize(updated)}

# -------- RATING --------

@sett.get("/rating")
async def get_rating(user: dict = Depends(auth_user_fb)):
    doc = get_or_create_rating(user["uid"])
    return serialize(doc)

@sett.put("/rating")

async def update_rating(payload: RatingUpdate, user: dict = Depends(auth_user_fb)):
    spdb = await db()

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


# async def update_rating(payload: RatingUpdate, user: dict = Depends(auth_user_fb)):
#     spdb = await db()
#     if payload.rating < 1 or payload.rating > 5:
#         raise HTTPException(status_code=400, detail="rating must be 1–5")
#     doc = get_or_create_rating(user["uid"])
#     doc_id = doc["_id"]
#     try:
#         await spdb.rating_col.update_one(
#             {"_id": doc_id}, {"$set": {"rating": payload.rating}}
#         )
#         updated = await spdb.rating_col.find_one({"_id": doc_id})
#     except PyMongoError as e:
#         logger.error(f"rating update/find error: {e}")
#         raise HTTPException(status_code=503, detail="Database error")
#     return {
#         "message": "Rating updated",
#         "rating": serialize(updated),
#     }

# -------- SUPPORT --------

@sett.get("/support")
async def get_support(user: dict = Depends(auth_user_fb)):
    doc = get_or_create_support(user["uid"])
    return serialize(doc)

# @sett.put("/support")
# async def update_support(payload: SupportUpdate, user: dict = Depends(auth_user_fb)):
#     spdb = await db()
#     # doc = get_or_create_support(user["uid"])
#     # doc_id = doc["_id"]
#     try:
#         await spdb.support_col.update_one(
#             {"firebase_uid": user["uid"]}, {"$set": {"message": payload.message}},
#             upsert=True
#         )
#         updated = await spdb.support_col.find_one({"firebase_uid": user["uid"]})
#     except PyMongoError as e:
#         logger.error(f"support update/find error: {e}")
#         raise HTTPException(status_code=503, detail="Database error")
#     return {
#         "message": "Support message updated",
#         "support": serialize(updated),
#     }



@sett.put("/support")
async def update_support(payload: SupportUpdate, user: dict = Depends(auth_user_fb)):
    spdb = await db()

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
    
    
from pydantic import BaseModel

class GenSupport(BaseModel):
    name: str
    email: str
    message: str
    

@sett.put("/general-support")
async def update_general_support(payload: GenSupport):
    spdb = await db()

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


class FeedbackSubmit(BaseModel):
    emotion : int
    emotionLabel : str
    
from datetime import datetime

@sett.post('/feedback-submit')
async def submitFeedback(payload : FeedbackSubmit, user : dict = Depends(auth_user_fb)):
    uid = user["uid"]
    spdb = await db()
    
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
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from bson import ObjectId

notification_router = APIRouter()

@notification_router.get("/getAll")
async def get_notifications(current_user = Depends(auth_user_fb)):
    ndb = get_db()
    notifications = await ndb.notifications.find({"firebase_uid": current_user["uid"]}).sort("timestamp", -1).limit(50).to_list(50)
    for n in notifications:
        n["id"] = str(n["_id"])
        del n["_id"]
    return notifications

@notification_router.patch("/{id}/read")
async def mark_read(id: str, current_user = Depends(auth_user_fb) ):
    ndb = get_db()
    result = await ndb.notifications.update_one(
        {"_id": ObjectId(id), "firebase_uid": current_user["uid"]},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        return {"message": "Notification not found"}
    return {"message": "Marked as read"}

@notification_router.patch("/read-all")
async def mark_all_read(current_user = Depends(auth_user_fb)):
    ndb = get_db()
    result = await ndb.notifications.update_many(
        {"firebase_uid": current_user["uid"], "read": False},
        {"$set": {"read": True}}
    )
    return {"message": f"Marked {result.modified_count} notifications as read"}

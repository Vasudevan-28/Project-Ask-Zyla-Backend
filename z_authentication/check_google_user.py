from fastapi import APIRouter
from authModels import GoogleEmailCheck
from utils.db import get_db
from firebase_admin_init import *

chk_ggle = APIRouter()

@chk_ggle.post("/check-google-user")
async def check_google_user(data: GoogleEmailCheck):
    db = get_db()
    users_col = db["users"]
    user = await users_col.find_one({"email": data.email})

    if user:
        return {
            "exists": True,
            "skin_profile": user.get("skin_profile", False)  
        }

    return {
        "exists": False,
        "skin_profile": None  
    }
from fastapi import Depends, HTTPException, APIRouter
# from firebase_admin import auth as firebase_auth
from utils.db import get_db
from utils._auth_firebase import auth_user_fb

fetch_me_router = APIRouter()

@fetch_me_router.get("/me")
async def get_me(user_data = Depends(auth_user_fb)):
    db = get_db()
    users_col = db["users"]
    
    uid = user_data.get("uid")

    # user = await users_col.find_one({"firebase_uid": uid})
    user = await users_col.find_one(
    {"firebase_uid": uid},
    {"_id": 0, "registered": 1, "skin_profile": 1})

    if not user:
        # raise HTTPException(status_code=404, detail="User not found")
        return {
            "exists" : False,
            "registered": False,
  "skin_profile": False
        }
    return {
         "exists": True,
        "registered": user.get("registered", False),
        "skin_profile": user.get("skin_profile", False),
    }

from fastapi import  HTTPException, APIRouter, Depends
from authModels import SetNewPassword
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from utils.auth_helpers import hash_password
from firebase_admin import auth

set_new_pass_router = APIRouter()


@set_new_pass_router.post("/set-new-pass")
async def reset_password_email(data: SetNewPassword, users= Depends(auth_user_fb)):
    db = get_db()
    users_col = db["users"]
    
    user_email = users.get("email")
    
    user = await users_col.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(data.new_password)

    
    try:
        firebase_uid = users.get("uid")
        if firebase_uid:
            auth.update_user(firebase_uid, password=data.new_password)
        else:
            fb_user = auth.get_user_by_email(user_email)
            auth.update_user(fb_user.uid, password=data.new_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Firebase password: {e}")

    
    await users_col.update_one(
        {"email": user_email},
        {"$set": {"password": hashed_pw, "otp": None, "otp_expiry": None}}
    )

    return {"message": "Password updated"}


from fastapi import  HTTPException,  APIRouter
from authModels import ResetPasswordEmail
from utils.db import users_col
from utils.auth_helpers import hash_password
from firebase_admin_init import *
from firebase_admin import auth


reset_email_pass_router = APIRouter()

@reset_email_pass_router.post("/resetpassemail")
async def reset_password_email(data: ResetPasswordEmail):
    
    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    hashed_pw = hash_password(data.new_password)

    
    await users_col.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_pw, "otp": None, "otp_expiry": None}}
    )

    try:
        
        firebase_uid = user.get("firebase_uid")
        if firebase_uid:
            auth.update_user(firebase_uid, password=data.new_password)
        else:
            
            fb_user = auth.get_user_by_email(data.email)
            auth.update_user(fb_user.uid, password=data.new_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Firebase password: {e}")

    return {"message": "Password updated"}


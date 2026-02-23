from fastapi import  HTTPException,  APIRouter
from authModels import ForgotPasswordEmail
from utils.db import get_db
from utils.auth_helpers import hash_password
from firebase_admin import auth

forgot_email_pass_router = APIRouter()

@forgot_email_pass_router.post("/forgotpassemail")
async def reset_password_email(data: ForgotPasswordEmail):
    db = get_db()
    users_col = db["users"]
    
    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    hashed_pw = hash_password(data.new_password)


    try:
        
        firebase_uid = user.get("firebase_uid")
        if firebase_uid:
            auth.update_user(firebase_uid, password=data.new_password)
        else:
            
            fb_user = auth.get_user_by_email(data.email)
            auth.update_user(fb_user.uid, password=data.new_password)
            
        await users_col.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_pw, "otp": None, "otp_expiry": None}}
    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Firebase password: {e}")

    return {"message": "Password updated"}


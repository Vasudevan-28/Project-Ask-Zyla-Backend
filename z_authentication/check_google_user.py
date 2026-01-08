from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from authModels import EmailOtpVerify, EmailRequest,GoogleEmailCheck, LoginModel, OTPVerify, PhoneOtpAttempt, PhoneRequest, ResetPasswordEmail, ResetPasswordPhone, SaveToken, SaveUserModel,SignUpModel
from utils.db import users_col, skin_col, backup_users
from utils.auth_helpers import hash_password, verify_password, generate_otp, otp_expiry
from firebase_admin_init import *

chk_ggle = APIRouter()

@chk_ggle.post("/check-google-user")
async def check_google_user(data: GoogleEmailCheck):
    user = await users_col.find_one({"email": data.email})

    if user:
        return {
            "exists": True,
            "skin_profile": user.get("skin_profile", False)  
        }

    return {
        "exists": False,
        "skin_profile": None  # 
    }
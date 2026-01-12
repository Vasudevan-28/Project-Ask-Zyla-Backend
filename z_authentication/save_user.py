from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from authModels import EmailOtpVerify, EmailRequest,GoogleEmailCheck, LoginModel, OTPVerify, PhoneOtpAttempt, PhoneRequest, ResetPasswordEmail, ResetPasswordPhone, SaveToken, SaveUserModel,SignUpModel
# from utils.db import users_col, skin_col, backup_users
from utils.db import get_db
from utils.auth_helpers import hash_password, verify_password, generate_otp, otp_expiry
from firebase_admin_init import *
from firebase_admin import auth
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta, timezone
import pytz
from dateutil import parser
from chatAppRoute import chatApp

save_user_router = APIRouter()

@save_user_router.post("/save-user")
async def save_user(data: dict):
    db = get_db()
    users_col = db["users"]

    existed = await users_col.find_one({"email": data["email"]})

    if existed:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    existed_phone = await users_col.find_one({"phone": data["phone"]})
    if existed_phone:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    data["cred_pass"] = data["password"]
    data["password"] = hash_password(data["password"])
    
    data["registered_at"] = datetime.now(timezone.utc)

    await users_col.insert_one(data)

    return {"message": "User saved successfully"}
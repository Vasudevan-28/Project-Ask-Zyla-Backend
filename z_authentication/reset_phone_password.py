from fastapi import APIRouter
from authModels import  ResetPasswordPhone
from utils.db import users_col
from utils.auth_helpers import hash_password


reset_phone_pass_router = APIRouter()

@reset_phone_pass_router.post("/reset-password-phone")
async def reset_password_phone(data: ResetPasswordPhone):

    hashed_pw = hash_password(data.new_password)

    await users_col.update_one(
        {"phone": data.phone},
        {"$set": {"password": hashed_pw, "otp": None}}
    )

    return {"message": "Password updated successfully!"}
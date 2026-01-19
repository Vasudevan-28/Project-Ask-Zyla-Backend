from fastapi import APIRouter
from authModels import  ResetPasswordPhone
from utils.db import get_db
from utils.auth_helpers import hash_password


reset_phone_pass_router = APIRouter()

@reset_phone_pass_router.post("/reset-password-phone")
async def reset_password_phone(data: ResetPasswordPhone):
    db = get_db()
    users_col = db["users"]

    hashed_pw = hash_password(data.new_password)

    await users_col.update_one(
        {"phone": data.phone},
        {"$set": {"password": hashed_pw, "otp": None}}
    )

    return {"message": "Password updated successfully!"}
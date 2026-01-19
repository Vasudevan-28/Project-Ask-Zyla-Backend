from fastapi import HTTPException, APIRouter
from authModels import  PhoneOtpAttempt
from utils.db import get_db
from z_authentication.timezone_helper import make_tz_aware, IST

from datetime import datetime, timedelta

ph_otp_attempt_router = APIRouter()

@ph_otp_attempt_router.post("/phone-otp-attempt")
async def phone_otp_attempt(data: PhoneOtpAttempt):
    db = get_db()
    users_col = db["users"]

    user = await users_col.find_one({"phone": data.phone})
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not found")

    now = datetime.now(IST)

    attempts = user.get("phone_otp_attempts", 0)
    block_until = make_tz_aware(user.get("phone_otp_block_until"))
    last_attempt = make_tz_aware(user.get("phone_otp_last_attempt"))


    # If still blocked
    if block_until and now < block_until:
        raise HTTPException(
            status_code=429,
            detail="Too many OTP requests. Try again after 30 minutes."
        )

    # Reset attempts if last was long ago (>30 min)
    if last_attempt and (now - last_attempt) > timedelta(minutes=30):
        attempts = 0


    if attempts >= 3:
        block_until = now + timedelta(minutes=30)
        await users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "phone_otp_block_until": block_until,
                    "phone_otp_attempts": attempts,
                    "phone_otp_last_attempt": now,
                }
            },
        )
        raise HTTPException(
            status_code=429,
            detail="Too many OTP requests. Try again after 30 minutes."
        )

    # Count this as an allowed attempt
    await users_col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "phone_otp_attempts": attempts + 1,
                "phone_otp_last_attempt": now,
                "phone_otp_block_until": None,
            }
        },
    )

    return {"message": "OK"}

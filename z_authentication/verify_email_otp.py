from fastapi import  HTTPException, APIRouter
from authModels import EmailOtpVerify
from utils.db import get_db
from z_authentication.timezone_helper import make_tz_aware, IST
from datetime import datetime

verify_otp_router = APIRouter()

@verify_otp_router.post("/verify-email-otp")
async def verify_email_otp(data: EmailOtpVerify):
    db = get_db()
    users_col = db["users"]

    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    stored_otp = user.get("otp")

    if stored_otp is None:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")

    try:
        stored_otp = int(stored_otp)
    except:
        raise HTTPException(status_code=500, detail="Stored OTP corrupt")

    if stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    expiry_value = user.get("otp_expiry")

    if expiry_value is None:
        raise HTTPException(status_code=400, detail="No OTP expiry stored")

    expiry = make_tz_aware(expiry_value)
    if expiry is None:
        raise HTTPException(status_code=500, detail="Could not parse stored expiry timestamp")

    now = datetime.now(IST)

    if now > expiry:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    await users_col.update_one(
        {"email": data.email},
        {
            "$set": {
                "otp": None,
                "otp_expiry": None,
                "email_otp_attempts": 0,
                "email_otp_block_until": None,
                "email_otp_last_attempt": None,
            }
        },
    )

    return {"message": "OTP verified"}

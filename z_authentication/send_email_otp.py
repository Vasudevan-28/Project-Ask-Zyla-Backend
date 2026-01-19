from fastapi import HTTPException, APIRouter
from authModels import EmailRequest
from utils.db import get_db
from utils.auth_helpers import generate_otp
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta
import pytz
from z_authentication.timezone_helper import make_tz_aware

seo_router = APIRouter()

IST = pytz.timezone("Asia/Kolkata")

@seo_router.post("/send-email-otp")
async def send_email_otp(data: EmailRequest):
    db = get_db()
    users_col = db["users"]

    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    
    now = datetime.now(IST)

    # ---- Rate limit logic (3 attempts → 30 min block) ----
    attempts = user.get("email_otp_attempts", 0)
    last_attempt = make_tz_aware(user.get("email_otp_last_attempt"))
    block_until = make_tz_aware(user.get("email_otp_block_until"))
    block_until = make_tz_aware(block_until)

    # If still blocked
    if block_until and now < block_until:
        raise HTTPException(
            status_code=429,
            detail="Too many OTP requests. Try again after 30 minutes."
        )

    # If last attempt was long ago (more than 30 min), reset attempts
    if last_attempt and (now - last_attempt) > timedelta(minutes=30):
        attempts = 0


    # Already hit 3 attempts in this window → start block
    if attempts >= 3:
        block_until = now + timedelta(minutes=30)
        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email_otp_block_until": block_until,
                    "email_otp_attempts": attempts,
                    "email_otp_last_attempt": now,
                }
            },
        )
        raise HTTPException(
            status_code=429,
            detail="Too many OTP requests. Try again after 30 minutes."
        )

    # ---- Generate OTP & expiry (3 minutes) ----
    otp_code = generate_otp()
    expiry_dt = now + timedelta(minutes=3)

    await users_col.update_one(
        {"email": data.email},
        {
            "$set": {
                "otp": otp_code,
                "otp_expiry": expiry_dt,
                "email_otp_attempts": attempts + 1,
                "email_otp_last_attempt": now,
                # clear block once we allow this request
                "email_otp_block_until": None,
            }
        }
    )

    sender = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    
    msg = MIMEText(f"Your OTP for resetting password is: {otp_code}\nValid for 3 minutes.")
    msg["Subject"] = "Beauty Sanctuary Email OTP"
    msg["From"] = sender
    msg["To"] = data.email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, data.email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {e}")

    return {"message": "OTP sent to email", "otp_expiry": expiry_dt.isoformat()}
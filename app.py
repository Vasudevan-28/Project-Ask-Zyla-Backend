from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.db import users_col, skin_col, backup_users
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

# from z_dashboard.routers import products, todos, auth

from z_dashboard.products import prrouter
from z_dashboard.todos import torouter
from notifications import ntrouter

from clearCache import clearrt

from settings import sett

app = FastAPI()

# CORS

# app = APIRouter(
#     prefix="/auth",      
#     tags=["Auth Module"] )

app.include_router(chatApp)

app.include_router(prrouter, tags=["products"])
app.include_router(torouter, tags=["todos"])

app.include_router(sett, tags=["settings"])

app.include_router(ntrouter)

app.include_router(clearrt, tags=["sensitive"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IST = pytz.timezone("Asia/Kolkata")

def make_tz_aware(dt):
    """
    Normalize values coming back from Mongo:
    - They are usually naive datetimes that actually represent UTC
    - Or ISO strings
    We convert them to IST-aware datetimes.
    """
    if dt is None:
        return None

    # If stored as string (ISO)
    if isinstance(dt, str):
        try:
            dt = parser.isoparse(dt)
        except Exception:
            return None

    # If naive, treat as UTC from Mongo and convert to IST
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST)



# ----------------------
#  MODELS
# ----------------------

class SaveUserModel(BaseModel):
    name: str
    email: str
    phone: str
    firebase_uid: str
    password: str   
    created_at: str


class SignUpModel(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    firebase_uid: str


class LoginModel(BaseModel):
    identifier: str   # email or phone
    password: str


class EmailRequest(BaseModel):
    email: str


class PhoneRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: int


class ResetPasswordPhone(BaseModel):
    phone: str
    new_password: str


class ResetPasswordEmail(BaseModel):
    email: str
    new_password: str    


class EmailOtpVerify(BaseModel):
    email: str
    otp: int


class PhoneOtpAttempt(BaseModel):
    phone: str


class SaveToken(BaseModel):
    email: str
    fcm_token: str


class GoogleEmailCheck(BaseModel):
    email: str




from reminder_service import start_reminder_loop
import asyncio

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_reminder_loop())

@app.get("/")
async def root():
    return {"message": "Backend successfully deployed"}


@app.post("/check-google-user")
async def check_google_user(data: GoogleEmailCheck):
    user = await users_col.find_one({"email": data.email})

    if user:
        return {
            "exists": True,
            "skin_profile": user.get("skin_profile", False)  # default = False
        }

    return {
        "exists": False,
        "skin_profile": None  # or False if you prefer
    }


# ----------------------
# SAVE USER (Signup from React)
# ----------------------
@app.post("/save-user")
async def save_user(data: dict):

    existed = await users_col.find_one({"email": data["email"]})

    if existed:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    existed_phone = await users_col.find_one({"phone": data["phone"]})
    if existed_phone:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    hashed_pw = hash_password(data["password"])

    await users_col.insert_one(data)

    return {"message": "User saved successfully"}


@app.post("/signup")
async def signup(data: SignUpModel):

    # 1️⃣ Must await async MongoDB call
    existing_user = await users_col.find_one({"email": data.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    existing_phone = await users_col.find_one({"phone" : data.phone})
    
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    hashed_pw = hash_password(data.password)

    # 2️⃣ Must await insert too
    await users_col.insert_one({
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "password": hashed_pw,
        "firebase_uid": data.firebase_uid,
        "skin_profile" : False,
        "otp": None,
        "otp_expiry": None,
        "fcm_token": None
    })

    return {"message": "Signup successful"}


# ----------------------
# LOGIN
# ----------------------
@app.post("/login")
async def login(data: LoginModel, request: Request = None):

    identifier = data.identifier.strip()

    # Determine login method
    if "@" in identifier:
        user = await users_col.find_one({"email": identifier})
        method = "email"
    else:
        user = await users_col.find_one({"phone": identifier})
        method = "phone"

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch firebase user info
    firebase_data = auth.get_user(user["firebase_uid"])

    # Block unverified email login
    if method == "email" and not firebase_data.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    
    # Verify password (bcrypt check)
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    now = datetime.utcnow()

    # Update login metadata
    await users_col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "last_login": now,
                "login_method": method,
                "email_verified": firebase_data.email_verified
            },
            "$push": {
                "login_history": {"at": now, "method": method}
            }
        }
    )

    # Send login email
    try:
        sender = os.getenv("SMTP_EMAIL")
        password = os.getenv("SMTP_PASSWORD")
        # sender = "forytpremi22@gmail.com"
        # password = "wusd grym ucgt xbat"
        recipient = user.get("email")

        if recipient:
            msg = MIMEText(
                f"Hello {user.get('name','')},\n\n"
                f"You logged in successfully at {now.isoformat()} UTC.\n"
                f"If this was not you, please reset your password."
            )
            msg["Subject"] = "Login notification"
            msg["From"] = sender
            msg["To"] = recipient

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())

    except Exception as e:
        print("Email error maillll :", e)
    
    skinpro = user.get("skin_profile", False)

    return {"message": "success", "method": method, "skin_profile": skinpro}

# ----------------------
# SEND EMAIL OTP (returns expiry)
# ----------------------  
@app.post("/send-email-otp")
async def send_email_otp(data: EmailRequest):
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

    # sender = "forytpremi22@gmail.com"
    # password = "wusd grym ucgt xbat"
    
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


        
    
    # Frontend uses otp_expiry for countdown
    return {"message": "OTP sent to email", "otp_expiry": expiry_dt.isoformat()}

class PhoneRequest(BaseModel):
    phone: str

@app.post("/getemailforphone")
async def get_email_for_phone(payload : PhoneRequest):
    phone = payload.phone
    user = await users_col.find_one({"phone" : phone})
    
    if not user:
        raise HTTPException(status_code=400, detail="Phone number not exist")
    
    user_email = user.get("email")
    print(user_email)
    
    return {"email" : user_email}
    

# ----------------------
# VERIFY EMAIL OTP (checks expiry)
# ----------------------
@app.post("/verify-email-otp")
async def verify_email_otp(data: EmailOtpVerify):
    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # --- OTP stored inside Mongo ---
    stored_otp = user.get("otp")

    # make sure OTP exists
    if stored_otp is None:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")

    # convert to int (if accidentally stored as string)
    try:
        stored_otp = int(stored_otp)
    except:
        raise HTTPException(status_code=500, detail="Stored OTP corrupt")

    # User-entered OTP must match
    if stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # --- EXPIRY FIX HERE ---
    expiry_value = user.get("otp_expiry")

    if expiry_value is None:
        raise HTTPException(status_code=400, detail="No OTP expiry stored")

    # Use the same normalizer we use elsewhere
    expiry = make_tz_aware(expiry_value)
    if expiry is None:
        raise HTTPException(status_code=500, detail="Could not parse stored expiry timestamp")

    # timezone-aware current time
    now = datetime.now(IST)

    # if now > expiry:
    #     raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    # --- Reset OTP after successful verification ---
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



@app.post("/phone-otp-attempt")
async def phone_otp_attempt(data: PhoneOtpAttempt):
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



# ----------------------
# RESET PASSWORD WITH PHONE
# ----------------------
@app.post("/reset-password-phone")
async def reset_password_phone(data: ResetPasswordPhone):

    hashed_pw = hash_password(data.new_password)

    await users_col.update_one(
        {"phone": data.phone},
        {"$set": {"password": hashed_pw, "otp": None}}
    )

    return {"message": "Password updated successfully!"}


# ----------------------
# RESET PASSWORD WITH EMAIL
# ----------------------
# ----------------------
@app.post("/resetpassemail")
async def reset_password_email(data: ResetPasswordEmail):
    # 1) Find user in MongoDB
    user = await users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Hash password for MongoDB storage
    hashed_pw = hash_password(data.new_password)

    # 3) Update MongoDB
    await users_col.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_pw, "otp": None, "otp_expiry": None}}
    )

    # 4) Update Firebase Auth using Admin SDK (so client doesn't need to be signed-in)
    try:
        # Prefer stored firebase_uid if available
        firebase_uid = user.get("firebase_uid")
        if firebase_uid:
            auth.update_user(firebase_uid, password=data.new_password)
        else:
            # Fallback: find user by email in Firebase
            fb_user = auth.get_user_by_email(data.email)
            auth.update_user(fb_user.uid, password=data.new_password)
    except Exception as e:
        # If Firebase update fails, we return a 500 so you can see the issue.
        # Optionally you could return success for DB and log the Firebase error.
        raise HTTPException(status_code=500, detail=f"Failed to update Firebase password: {e}")

    return {"message": "Password updated"}


# @app.post("/delete-account")
# async def delete_account(data: EmailRequest):
#     user = await users_col.find_one({"email": data.email})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     await users_col.delete_one({"email": data.email})

#     return {"message": "Account deleted"}

from datetime import datetime
from fastapi import HTTPException

@app.post("/delete-account")
async def delete_account(data: EmailRequest):
    user = await users_col.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_deleted_at"] = str(datetime.now())

    await backup_users.insert_one(user)

    await users_col.delete_one({"email": data.email})

    return {"message": "Account deleted successfully"}



# ----------------------
# SAVE FCM TOKEN
# ----------------------
@app.post("/save-token")
def save_token(data: SaveToken):

    users_col.update_one(
        {"email": data.email},
        {"$set": {"fcm_token": data.fcm_token}}
    )

    return {"message": "Token saved"}


@app.get("/")
def home():
    return {"message": "FastAPI Running!"}


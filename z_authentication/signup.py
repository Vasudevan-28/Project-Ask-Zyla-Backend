from fastapi import HTTPException, APIRouter, Depends
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from utils.auth_helpers import hash_password

from datetime import datetime, timezone

signup_router = APIRouter()

@signup_router.post("/signup")
async def signup(data: dict, user = Depends(auth_user_fb)):
    db = get_db()
    users_col = db["users"]
    
    user_uid = user.get("uid")

    existing_user = await users_col.find_one({"email": data["email"]})

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    existing_phone = await users_col.find_one({"phone" : data["phone"]})
    
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    data["cred_pass"] = data["password"]
    data["password"] = hash_password(data["password"])
    data["firebase_uid"] = user_uid
    # data["registered"] = False
    data["registered_at"] = datetime.now(timezone.utc)

    
    # await users_col.insert_one({
    #     "name": data.name,
    #     "email": data.email,
    #     "dob" : data.dob,
    #     "phone": data.phone,
    #     "password": hashed_pw,
    #     "firebase_uid": data.firebase_uid,
    #     "skin_profile" : False,
    #     "otp": None,
    #     "otp_expiry": None,
    #     "fcm_token": None
    # })
    
    await users_col.insert_one(data)

    return {"message": "Signup successful"}

from fastapi import HTTPException, APIRouter, Depends
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from utils.auth_helpers import hash_password
from datetime import datetime, timezone

save_user_router = APIRouter()

@save_user_router.post("/save-user")
async def save_user(data: dict, user= Depends(auth_user_fb)):
    db = get_db()
    users_col = db["users"]

    user_uid = user.get("uid")
    user_email = user.get("email")

    # existed = await users_col.find_one({"email": data["email"]})
    existed = await users_col.find_one({"email": user_email })

    if existed:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    existed_phone = await users_col.find_one({"phone": data["phone"]})
    if existed_phone:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    data["cred_pass"] = data["password"]
    data["password"] = hash_password(data["password"])
    data["firebase_uid"] = user_uid
    
    data["registered_at"] = datetime.now(timezone.utc)

    await users_col.insert_one(data)

    return {"message": "User saved successfully"}
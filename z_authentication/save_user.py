from fastapi import HTTPException, APIRouter
from utils.db import get_db
from utils.auth_helpers import hash_password
from datetime import datetime, timezone

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
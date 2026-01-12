from fastapi import HTTPException, APIRouter

from authModels import PhoneRequest
# from utils.db import users_col
from utils.db import get_db
from firebase_admin_init import *


get_email_phone_router = APIRouter()

@get_email_phone_router.post("/getemailforphone")
async def get_email_for_phone(payload : PhoneRequest):
    db = get_db()
    users_col = db["users"]
    phone = payload.phone
    user = await users_col.find_one({"phone" : phone})
    
    if not user:
        raise HTTPException(status_code=400, detail="Phone number not exist")
    
    user_email = user.get("email")
    print(user_email)
    
    return {"email" : user_email}
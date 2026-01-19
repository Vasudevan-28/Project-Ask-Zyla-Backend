from fastapi import HTTPException, APIRouter
from authModels import PhoneRequest
from utils.db import get_db

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
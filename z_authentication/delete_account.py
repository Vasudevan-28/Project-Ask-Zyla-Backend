
from fastapi import HTTPException, APIRouter, Depends
# from authModels import EmailRequest
from utils.db import get_db, get_bkdb
from utils._auth_firebase import auth_user_fb
from datetime import datetime
from firebase_admin import auth

delete_account_router = APIRouter()

@delete_account_router.post("/delete-account")
async def delete_account(user_data= Depends(auth_user_fb)):
    db = get_db()
    users_col = db["users"]
    
    user_email = user_data.get("email")
    user_uid = user_data.get("uid")
    
    bkdb = get_bkdb()
    backup_users = bkdb["users_del"]
    # user = await users_col.find_one({"email": user_email})
    user = await users_col.find_one({"firebase_uid": user_uid})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_deleted_at"] = str(datetime.now())

    await backup_users.insert_one(user)

    await users_col.delete_one({"firebase_uid": user_uid})
    auth.delete_user(user_uid)

    return {"message": "Account deleted successfully"}

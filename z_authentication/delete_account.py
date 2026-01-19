
from fastapi import HTTPException, APIRouter
from authModels import EmailRequest
from utils.db import get_db, get_bkdb
from datetime import datetime

delete_account_router = APIRouter()

@delete_account_router.post("/delete-account")
async def delete_account(data: EmailRequest):
    db = get_db()
    users_col = db["users"]
    
    bkdb = get_bkdb()
    backup_users = bkdb["users_del"]
    user = await users_col.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_deleted_at"] = str(datetime.now())

    await backup_users.insert_one(user)

    await users_col.delete_one({"email": data.email})

    return {"message": "Account deleted successfully"}

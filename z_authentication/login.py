
from fastapi import FastAPI, HTTPException, Request, APIRouter
from authModels import  LoginModel
# from utils.db import users_col
from utils.db import get_db
from utils.auth_helpers import verify_password
from firebase_admin import auth
from datetime import datetime

login_router = APIRouter()

@login_router.post("/login")
async def login(data: LoginModel, request: Request = None):
    db = get_db()
    users_col = db["users"]

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
    # if data.password == user["password"]:
    #     raise HTTPException(status_code=401, detail="Invalid password")

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

    
    skinpro = user.get("skin_profile", False)

    return {"message": "success", "method": method, "skin_profile": skinpro}






    # Send login email
    # try:
    #     sender = os.getenv("SMTP_EMAIL")
    #     password = os.getenv("SMTP_PASSWORD")
    #     # sender = "forytpremi22@gmail.com"
    #     # password = "wusd grym ucgt xbat"
    #     recipient = user.get("email")

    #     if recipient:
    #         msg = MIMEText(
    #             f"Hello {user.get('name','')},\n\n"
    #             f"You logged in successfully at {now.isoformat()} UTC.\n"
    #             f"If this was not you, please reset your password."
    #         )
    #         msg["Subject"] = "Login notification"
    #         msg["From"] = sender
    #         msg["To"] = recipient

    #         with smtplib.SMTP("smtp.gmail.com", 587) as server:
    #             server.starttls()
    #             server.login(sender, password)
    #             server.sendmail(sender, recipient, msg.as_string())

    # except Exception as e:
    #     print("Email error maillll :", e)
from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field
from fastapi import Header, HTTPException
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from starlette.status import HTTP_401_UNAUTHORIZED

# from z_chatbot_module.memory import db
from utils.db import get_db

import base64

load_dotenv()

b64 = os.getenv("FIREBASE_CONFIG_BASE64")

decoded = base64.b64decode(b64).decode("utf-8")
config = json.loads(decoded)


if not firebase_admin._apps:
    
    # cred = credentials.Certificate("firebase-service-key.json")
    cred = credentials.Certificate(config)
    firebase_admin.initialize_app(cred)

def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        print("header_mistake")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        print("format mistake")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header format")
    return parts[1]

def verify_firebase_token_sync(id_token: str) -> Dict[str, Any]:
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        print("invalid or expire")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired Firebase ID token")

async def auth_user_fb(authorization: Optional[str] = Header(None)):
    token = _extract_bearer(authorization)
    # print(authorization)
    decoded = verify_firebase_token_sync(token)
    uid = decoded.get("uid")
    if not uid:
        
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token payload: missing uid")

    # try:
    #     fdb = get_db()
    #     now = datetime.now(timezone.utc).isoformat()
    #     doc = {
    #         "uid": uid,
    #         "email": decoded.get("email"),
    #         "name": decoded.get("name") or decoded.get("display_name") or "",
    #         "lastSeenAt": now,
    #         "updatedAt": now,
    #     }
    #     update = {
    #         "$set": doc,
    #         "$setOnInsert": {"createdAt": now},
    #     }
    #     await fdb.usersfb.update_one({"uid": uid}, update, upsert=True)
    # except Exception:
        # pass

    return {"uid": uid, "email": decoded.get("email"), "name": decoded.get("name") or decoded.get("display_name")}


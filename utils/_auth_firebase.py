from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field
from fastapi import Header, HTTPException, Depends, Request
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_500_INTERNAL_SERVER_ERROR

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

class UserCreateFB(BaseModel):
    uid: str = Field(..., example="firebase-uid-xxx")
    email: EmailStr
    name: Optional[str] = Field("", example="Full Name")

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

    try:
        fdb = get_db()
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "uid": uid,
            "email": decoded.get("email"),
            "name": decoded.get("name") or decoded.get("display_name") or "",
            "lastSeenAt": now,
            "updatedAt": now,
        }
        update = {
            "$set": doc,
            "$setOnInsert": {"createdAt": now},
        }
        await fdb.usersfb.update_one({"uid": uid}, update, upsert=True)
    except Exception:
        pass

    return {"uid": uid, "email": decoded.get("email"), "name": decoded.get("name") or decoded.get("display_name")}

async def create_user_record_fb(uid: str, email: str, name: str = "") -> Dict[str, Any]:
    fdb = get_db()
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "uid": uid,
        "email": email,
        "name": name or "",
        "updatedAt": now,
    }
    update = {"$set": doc, "$setOnInsert": {"createdAt": now}}
    try:
        result = await fdb.usersfb.update_one({"uid": uid}, update, upsert=True)
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to write user to database")
    
    await fdb.profiles.update_one(
        {"uid": uid},
        {
            "$setOnInsert": {
                "uid": uid,
                "profile": {
                    "name": name,
                    "skin_type": None,
                    "concerns": [],
                    "allergies": [],
                    "avoid_ingredients": [],
                    "prefer_ingredients": [],
                    "budget_max": None,
                    "fragrance_free": None,
                },
                "created_at": now,
                "updated_at": now,
            }
        },
        upsert=True,
    )    
    
    return {
        "ok": True,
        "uid": uid,
        "inserted": bool(result.upserted_id),
        "matched_count": result.matched_count,
        "modified_count": result.modified_count,
    }

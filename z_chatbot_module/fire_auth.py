from __future__ import annotations
import os
import json
import time
from typing import Optional, Dict

from fastapi import Depends, HTTPException, Header
from pydantic import BaseModel

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from z_chatbot_module.db import db

API_KEY_BYTES = int(os.getenv("API_KEY_BYTES", "24"))


class UserCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


async def create_user_record(name: Optional[str], email: Optional[str]) -> Dict[str, str]:
    import secrets

    d = await db()
    uid = secrets.token_hex(12)
    api_key = secrets.token_urlsafe(API_KEY_BYTES)
    now = time.time()
    await d.users.insert_one(
        {"uid": uid, "api_key": api_key, "name": name, "email": email, "created_at": now, "updated_at": now}
    )
 
    await d.profiles.update_one(
        {"uid": uid},
        {
            "$setOnInsert": {
                "uid": uid,
                "profile": {
                    "name": None,
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
    return {"uid": uid, "api_key": api_key}


def _init_firebase_app():
    if firebase_admin._apps:
        return

    import json
    with open("firebase-service-key.json", "r", encoding="utf-8") as f:
        cred_dict = json.load(f)

    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)


async def _ensure_user_in_db(uid: str, name: Optional[str], email: Optional[str]):
    d = await db()
    now = time.time()
    await d.users.update_one(
        {"uid": uid},
        {
            "$set": {"name": name, "email": email, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    await d.profiles.update_one(
        {"uid": uid},
        {
            "$setOnInsert": {
                "uid": uid,
                "profile": {
                    "name": None,
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


async def auth_user(authorization: Optional[str] = Header(None)) -> Dict[str, str]:

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer Firebase ID token")

    token = authorization.split(" ", 1)[1].strip()

   
    if "." not in token:
        d = await db()
        user = await d.users.find_one({"api_key": token})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return {"uid": user["uid"], "name": user.get("name"), "email": user.get("email")}

    try:
        _init_firebase_app()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase init error: {e}")

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase ID token")

    uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name") or decoded.get("displayName") or decoded.get("fname") or None

    if not uid:
        raise HTTPException(status_code=401, detail="Invalid Firebase token (missing uid)")


    try:
        await _ensure_user_in_db(uid, name, email)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to ensure user record in DB")

    return {"uid": uid, "name": name, "email": email}
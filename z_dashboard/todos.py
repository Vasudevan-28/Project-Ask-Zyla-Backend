from fastapi import APIRouter, HTTPException, Body, Query, Depends, Header
from typing import List
from z_dashboard.dash_models import ToDoModel
from utils.db import get_db
from utils._auth_firebase import auth_user_fb
from bson import ObjectId
from starlette.status import HTTP_401_UNAUTHORIZED

torouter = APIRouter(prefix="/todoCall")

async def update_streak_for_date(date_str: str, uid: str):
    tdb = get_db()
    total = await tdb["todos"].count_documents({"date": date_str, "uid": uid})
    if total == 0:
        await tdb["streaks"].update_one(
            {"date": date_str, "uid": uid},
            {"$set": {"completed": False}},
            upsert=True
        )
        return

    completed_count = await tdb["todos"].count_documents({"date": date_str, "uid": uid, "checked": True})
    is_complete = (total == completed_count)
    
    await tdb["streaks"].update_one(
        {"date": date_str, "uid": uid},
        {"$set": {"completed": is_complete}},
        upsert=True
    )

@torouter.get("/todos", response_model=List[ToDoModel])
async def get_todos(date: str = Query(..., description="Date in YYYY-MM-DD format"), user=Depends(auth_user_fb)):
    tdb = get_db()
    todos = await tdb["todos"].find({"date": date, "uid": user["uid"]}).to_list(1000)
    return todos

@torouter.post("/todos", response_model=ToDoModel)
async def add_todo(todo: ToDoModel = Body(...), user=Depends(auth_user_fb)):
    tdb = get_db()
    todo_dict = todo.dict(by_alias=True, exclude={"id"})
    todo_dict['uid'] = user['uid']  # Ensure each todo is tagged with the user's UID

    new_todo = await tdb["todos"].insert_one(todo_dict)
    created_todo = await tdb["todos"].find_one({"_id": new_todo.inserted_id})
    
    await update_streak_for_date(created_todo["date"], user["uid"])
    return created_todo

@torouter.patch("/todos/{id}", response_model=ToDoModel)
async def update_todo(id: str, checked: bool = Body(..., embed=True), user=Depends(auth_user_fb)):
    tdb = get_db()
    existing = await tdb["todos"].find_one({"_id": ObjectId(id), "uid": user["uid"]})
    if not existing:
        raise HTTPException(status_code=404, detail="ToDo not found")

    update_result = await tdb["todos"].update_one(
        {"_id": ObjectId(id), "uid": user["uid"]}, {"$set": {"checked": checked}}
    )
    if update_result.modified_count == 1:
        updated_todo = await tdb["todos"].find_one({"_id": ObjectId(id), "uid": user["uid"]})
        await update_streak_for_date(updated_todo["date"], user["uid"])
        return updated_todo

    # If document exists but no changes, return existing
    existing = await tdb["todos"].find_one({"_id": ObjectId(id), "uid": user["uid"]})
    if existing:
        return existing
        
    raise HTTPException(status_code=404, detail="ToDo not found")

@torouter.delete("/todos/{id}")
async def delete_todo(id: str, user=Depends(auth_user_fb)):
    tdb = get_db()
    todo = await tdb["todos"].find_one({"_id": ObjectId(id), "uid": user["uid"]})
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
        
    delete_result = await tdb["todos"].delete_one({"_id": ObjectId(id), "uid": user["uid"]})
    if delete_result.deleted_count == 1:
        await update_streak_for_date(todo["date"], user["uid"])
        return {"message": "ToDo deleted"}
    raise HTTPException(status_code=404, detail="ToDo not found")

@torouter.get("/streak")
async def get_streak(user=Depends(auth_user_fb)):
    from datetime import datetime, timedelta
    tdb = get_db()
    # Only fetch streaks for this user!
    cursor = tdb["streaks"].find({"completed": True, "uid": user["uid"]}).sort("date", -1)
    completed_dates = await cursor.to_list(None)
    completed_set = {d["date"] for d in completed_dates}
    streak = 0
    today_date = datetime.now()
    today_str = today_date.strftime("%Y-%m-%d")
    yesterday_date = today_date - timedelta(days=1)
    yesterday_str = yesterday_date.strftime("%Y-%m-%d")
    if yesterday_str in completed_set:
        streak += 1
        cursor_date = yesterday_date - timedelta(days=1)
        for _ in range(365):
            d_str = cursor_date.strftime("%Y-%m-%d")
            if d_str in completed_set:
                streak += 1
                cursor_date -= timedelta(days=1)
            else:
                break
        if today_str in completed_set:
            streak += 1
    else:
        if today_str in completed_set:
            streak = 1
    return {"streak": streak}

@torouter.get("/completed-dates", response_model=List[str])
async def get_completed_dates(user = Depends(auth_user_fb)):
    tdb = get_db()
    cursor = tdb["streaks"].find({"uid": user["uid"], "completed": True})
    completed_docs = await cursor.to_list(None)
    return [doc["date"] for doc in completed_docs]
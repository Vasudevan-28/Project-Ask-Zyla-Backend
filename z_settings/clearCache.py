
from utils.db import db, bkdb
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from z_chatbot_module._auth_firebase import auth_user_fb

main_db = db
archive_db = bkdb

clear_router = APIRouter(prefix='/sensitive')

COLLECTION_FILTERS = {
    "conversations": lambda uid: {"uid": uid},
    "notifications": lambda uid: {"firebase_uid": uid},
    "products":      lambda uid: {"uid": uid},
    "streaks":       lambda uid: {"uid": uid},
    "summaries":     lambda uid: {"uid": uid},
    "messages":      lambda uid: {"uid": uid},
    "todos":         lambda uid: {"uid": uid},
    
    "skinData":      lambda uid: {"userId": uid},
}


async def backup_collection(
    collection_name: str,
    user_filter: Dict[str, Any],
    force_new_ids: bool = False,
) -> int:
  
    src_coll = main_db[collection_name]
    dst_coll = archive_db[collection_name]

    docs: List[Dict[str, Any]] = await src_coll.find(user_filter).to_list(None)
    if not docs:
        return 0

    now = datetime.utcnow()
    archived_docs = []
    for d in docs:
        doc_copy = dict(d)
        doc_copy["deleted_at"] = now

        if force_new_ids and "_id" in doc_copy:
            
            doc_copy.pop("_id")

        archived_docs.append(doc_copy)

    await dst_coll.insert_many(archived_docs)
    return len(archived_docs)


async def clear_non_skin_collection(
    collection_name: str,
    user_filter: Dict[str, Any],
) -> Dict[str, int]:
  
    backed_up_count = await backup_collection(collection_name, user_filter)
    deleted_result = await main_db[collection_name].delete_many(user_filter)
    return {
        "backed_up": backed_up_count,
        "deleted": deleted_result.deleted_count,
    }


async def clear_skin_data(uid: str) -> Dict[str, int]:
   
    collection_name = "skinData"
    user_filter = COLLECTION_FILTERS[collection_name](uid)
    src_coll = main_db[collection_name]

    backed_up_count = await backup_collection(
        collection_name,
        user_filter,
        force_new_ids=True,
    )

    doc = await src_coll.find_one(user_filter)
    if not doc:
        return {"backed_up": backed_up_count, "cleared_docs": 0}

    _id = doc["_id"]

    res = await src_coll.replace_one(
        {"_id": _id},
        {"_id": _id, "cleared": True, "userId": uid}
    )

    return {
        "backed_up": backed_up_count,
        "cleared_docs": res.modified_count,
    }


@clear_router.post("/clear_cache")
async def clear_cache(user=Depends(auth_user_fb)):
  
    uid = user["uid"]

    results: Dict[str, Dict[str, int]] = {}

    for collection_name, filter_builder in COLLECTION_FILTERS.items():
        user_filter = filter_builder(uid)

        if collection_name == "skinData":
            results[collection_name] = await clear_skin_data(uid)
        else:
            results[collection_name] = await clear_non_skin_collection(
                collection_name, user_filter
            )

    return JSONResponse(
        {
            "status": "success",
            "uid": uid,
            "details": results,
        }
    )

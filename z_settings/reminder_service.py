import asyncio
from datetime import datetime
# from ..database import get_database
from z_chatbot_module.db import db
# from .email_service import send_email
import logging

logger = logging.getLogger("uvicorn")

# async def check_reminders():
#     """
#     Checks for products with a reminder_time matching the current time
#     and sends email notifications.
#     """
#     ndb = await db()
#     now = datetime.now().strftime("%H:%M")
    
#     # Find products with matching reminder_time
#     # We might want to optimize this index later
#     products = await ndb.products.find({"reminder_time": now}).to_list(1000)
    
#     if products:
#         logger.info(f"Found {len(products)} reminders for {now}")
        
#     for product in products:
#         uid = product.get("uid")
#         if not uid:
#             continue
            
#         # Get user to find email
#         user = await ndb.users.find_one({"firebase_uid": uid})
#         if user :
#             product_name = product.get("name", "Routine Item")
#             # email = user["email"]
#             # subject = f"Reminder: {product_name}"
#             # body = f"It's time for your routine: {product_name}\n\n{product.get('desc', '')}"
            
#             # await send_email(email, subject, body)

#             # Create notification
#             await ndb.notifications.insert_one({
#                 "firebase_uid": uid,
#                 "title": "Routine Reminder",
#                 "message": f"It's time for: {product_name}",
#                 "timestamp": datetime.utcnow(),
#                 "read": False,
#                 "type": "reminder"
#             })
            
#             print("notifications updated")
#         else:
#             if not user:
#                 logger.warning(f"User {uid} not found for product {product.get('_id')}")
#             elif not user.get("email"):
#                 logger.debug(f"User {uid} has no email set. Skipping reminder.")


async def check_reminders():
    ndb = await db()
    now = datetime.utcnow().strftime("%H:%M")
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    products = await ndb.products.find({"reminder_time": now}).to_list(1000)

    for product in products:
        uid = product.get("uid")
        if not uid:
            continue

        existing = await ndb.notifications.find_one({
            "firebase_uid": uid,
            "type": "reminder",
            "source_id": str(product["_id"]),
            "date": today_str
        })
        if existing:
            continue

        await ndb.notifications.insert_one({
            "firebase_uid": uid,
            "title": "Routine Reminder",
            "message": f"It's time for: {product.get('name','Routine Item')}",
            "timestamp": datetime.utcnow(),
            "read": False,
            "type": "reminder",
            "source_id": str(product["_id"]),
            "date": today_str
        })
                

logger = logging.getLogger("uvicorn")

REMINDER_SLOTS = ("15:00", "21:00")  


async def check_todo_reminders():
 
    ndb = await db()
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    if current_time not in REMINDER_SLOTS:
        return

    today_str = now.strftime("%Y-%m-%d")

    # Fetch all incomplete todos for today
    todos = await ndb.todos.find({
        "date": today_str,
        "checked": False
    }).to_list(10_000)

    if not todos:
        logger.info(f"No incomplete todos for {today_str} at {current_time}")
        return

    # Group todos per user
    pending_per_user: dict[str, int] = {}
    for todo in todos:
        uid = todo.get("uid")
        if not uid:
            continue
        pending_per_user[uid] = pending_per_user.get(uid, 0) + 1

    logger.info(
        f"Found {len(pending_per_user)} users with incomplete todos "
        f"for {today_str} at {current_time}"
    )

    for uid, count in pending_per_user.items():
        user = await ndb.users.find_one({"firebase_uid": uid})
        if not user:
            logger.warning(f"User {uid} not found for todo reminder")
            continue

        plural = "todos" if count > 1 else "todo"
        message = (
            f"You still have {count} {plural} left for today. "
            "Complete them to maintain your streak!"
        )

        existing = await ndb.notifications.find_one({
            "firebase_uid": uid,
            "type": "todo_reminder",
            "date": today_str,
            "slot": current_time
        })
        if existing:
            continue

        await ndb.notifications.insert_one({
            "firebase_uid": uid,
            "title": "Todo Reminder",
            "message": message,
            "timestamp": datetime.utcnow(),
            "read": False,
            "type": "todo_reminder",
            "date": today_str,   
            "slot": current_time 
        })

        print("todo reminder notification inserted")


async def start_reminder_loop():
 
    logger.info("Starting reminder service loop...")
    print("Starting reminder service loop...")
    while True:
        # Calculate seconds until the next minute
        now = datetime.now()
        seconds_until_next_minute = 60 - now.second - (now.microsecond / 1_000_000)
        
        # Sleep until the start of the next minute (plus a tiny buffer)
        await asyncio.sleep(seconds_until_next_minute + 0.05)
        
        try:
            await check_reminders()
            
            await check_todo_reminders()
        except Exception as e:
            logger.error(f"Error in reminder loop: {e}")

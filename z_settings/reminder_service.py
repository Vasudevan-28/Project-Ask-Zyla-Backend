import asyncio
from datetime import datetime
from utils.db import get_db
import logging

logger = logging.getLogger("uvicorn")

async def check_reminders():

    ndb = get_db()
    # now = datetime.now().strftime("%H:%M")
    now = datetime.utcnow().strftime("%H:%M")
    logger.info(f"Server time is {datetime.utcnow().isoformat()}")

    products = await ndb.products.find({"reminder_time": now}).to_list(1000)
    
    if products:
        logger.info(f"Found {len(products)} reminders for {now}")
        
    for product in products:
        uid = product.get("uid")
        if not uid:
            continue
            
        # Get user to find email
        user = await ndb.users.find_one({"firebase_uid": uid})
        if user :
            product_name = product.get("name", "Routine Item")
            # email = user["email"]
            # subject = f"Reminder: {product_name}"
            # body = f"It's time for your routine: {product_name}\n\n{product.get('desc', '')}"
            
            # await send_email(email, subject, body)

            # Create notification
            await ndb.notifications.insert_one({
                "firebase_uid": uid,
                "title": "Routine Reminder",
                "message": f"It's time for: {product_name}",
                "timestamp": datetime.utcnow(),
                "read": False,
                "type": "reminder"
            })
            
            print("notifications updated")
        else:
            if not user:
                logger.warning(f"User {uid} not found for product {product.get('_id')}")
            elif not user.get("email"):
                logger.debug(f"User {uid} has no email set. Skipping reminder.")


# REMINDER_SLOTS = ("15:00", "21:00")  


# async def check_todo_reminders():
 
#     ndb = get_db()
#     # now = datetime.now()
#     # current_time = now.strftime("%H:%M")
    
#     now = datetime.utcnow()
#     current_time = now.strftime("%H:%M")
    
#     REMINDER_SLOTS = {"15:00", "21:00"}
#     current_minute = now.strftime("%H:%M")

#     if current_minute not in REMINDER_SLOTS:
#         return

#     today_str = now.strftime("%Y-%m-%d")

#     # Fetch all incomplete todos for today
#     todos = await ndb.todos.find({
#         "date": today_str,
#         "checked": False
#     }).to_list(10_000)

#     if not todos:
#         logger.info(f"No incomplete todos for {today_str} at {current_time}")
#         return

#     # Group todos per user
#     pending_per_user: dict[str, int] = {}
#     for todo in todos:
#         uid = todo.get("uid")
#         if not uid:
#             continue
#         pending_per_user[uid] = pending_per_user.get(uid, 0) + 1

#     logger.info(
#         f"Found {len(pending_per_user)} users with incomplete todos "
#         f"for {today_str} at {current_time}"
#     )

#     for uid, count in pending_per_user.items():
#         user = await ndb.users.find_one({"firebase_uid": uid})
#         if not user:
#             logger.warning(f"User {uid} not found for todo reminder")
#             continue

#         plural = "todos" if count > 1 else "todo"
#         message = (
#             f"You still have {count} {plural} left for today. "
#             "Complete them to maintain your streak!"
#         )

#         existing = await ndb.notifications.find_one({
#             "firebase_uid": uid,
#             "type": "todo_reminder",
#             "date": today_str,
#             "slot": current_time
#         })
#         if existing:
#             continue

#         await ndb.notifications.insert_one({
#             "firebase_uid": uid,
#             "title": "Todo Reminder",
#             "message": message,
#             "timestamp": datetime.utcnow(),
#             "read": False,
#             "type": "todo_reminder",
#             "date": today_str,   
#             "slot": current_time 
#         })

#         print("todo reminder notification inserted")


from datetime import datetime, timedelta

# UTC times corresponding to 15:00 and 21:00 IST
# REMINDER_SLOTS = [(9, 30), (15, 30)]
REMINDER_SLOTS = [(6, 45), (7, 10)]
TRIGGER_WINDOW = 5  # minutes safety window

async def check_todo_reminders():
    ndb = get_db()

    now = datetime.utcnow()
    now_minutes = now.hour * 60 + now.minute

    # Convert UTC -> IST
    ist_now = now + timedelta(hours=5, minutes=30)
    today_ist = ist_now.strftime("%Y-%m-%d")

    def in_window(h, m):
        slot_minutes = h * 60 + m
        return slot_minutes <= now_minutes < slot_minutes + TRIGGER_WINDOW

    matched_slot = None
    for h, m in REMINDER_SLOTS:
        if in_window(h, m):
            matched_slot = f"{h:02d}:{m:02d}"
            break

    if not matched_slot:
        return  # Not in any reminder window

    # Fetch today's IST todos
    todos = await ndb.todos.find({
        "date": today_ist,
        "checked": False
    }).to_list(10_000)

    if not todos:
        return

    # Group todos per user
    pending_per_user: dict[str, int] = {}
    for todo in todos:
        uid = todo.get("uid")
        if not uid:
            continue
        pending_per_user[uid] = pending_per_user.get(uid, 0) + 1

    for uid, count in pending_per_user.items():
        # Prevent duplicate for this slot
        existing = await ndb.notifications.find_one({
            "firebase_uid": uid,
            "type": "todo_reminder",
            "date": today_ist,
            "slot": matched_slot
        })
        if existing:
            continue

        user = await ndb.users.find_one({"firebase_uid": uid})
        if not user:
            continue

        plural = "todos" if count > 1 else "todo"
        message = (
            f"You still have {count} {plural} left for today. "
            "Complete them to maintain your streak!"
        )

        await ndb.notifications.insert_one({
            "firebase_uid": uid,
            "title": "Todo Reminder",
            "message": message,
            "timestamp": datetime.utcnow(),
            "read": False,
            "type": "todo_reminder",
            "date": today_ist,      # IST date
            "slot": matched_slot    # UTC slot (09:30 or 15:30)
        })

        print("Todo reminder inserted for", uid)


# async def start_reminder_loop():
 
#     logger.info("Starting reminder service loop...")
#     print("Starting reminder service loop...")
#     while True:
#         # Calculate seconds until the next minute
#         now = datetime.now()
#         seconds_until_next_minute = 60 - now.second - (now.microsecond / 1_000_000)
        
#         # Sleep until the start of the next minute (plus a tiny buffer)
#         await asyncio.sleep(seconds_until_next_minute + 0.05)
        
#         try:
#             await check_reminders()
            
#             await check_todo_reminders()
#         except Exception as e:
#             logger.error(f"Error in reminder loop: {e}")

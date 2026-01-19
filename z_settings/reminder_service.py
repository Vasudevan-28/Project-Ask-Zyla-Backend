from datetime import datetime, timedelta
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



REMINDER_SLOTS = [(9, 30), (15, 30)]
TRIGGER_WINDOW = 3

async def check_todo_reminders():
    ndb = get_db()

    now = datetime.utcnow()
    now_minutes = now.hour * 60 + now.minute

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
        return  

    todos = await ndb.todos.find({
        "date": today_ist,
        "checked": False
    }).to_list(10_000)

    if not todos:
        return

    pending_per_user: dict[str, int] = {}
    for todo in todos:
        uid = todo.get("uid")
        if not uid:
            continue
        pending_per_user[uid] = pending_per_user.get(uid, 0) + 1

    for uid, count in pending_per_user.items():
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
            "date": today_ist,      
            "slot": matched_slot    
        })

        print("Todo reminder inserted for", uid)


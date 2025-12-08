import asyncio
from datetime import datetime
# from ..database import get_database
from z_chatbot_module.db import db
# from .email_service import send_email
import logging

logger = logging.getLogger("uvicorn")

async def check_reminders():
    """
    Checks for products with a reminder_time matching the current time
    and sends email notifications.
    """
    ndb = await db()
    now = datetime.now().strftime("%H:%M")
    
    # Find products with matching reminder_time
    # We might want to optimize this index later
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

async def start_reminder_loop():
    """
    Starts the background loop to check for reminders every minute.
    """
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
        except Exception as e:
            logger.error(f"Error in reminder loop: {e}")

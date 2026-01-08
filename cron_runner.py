import asyncio
from z_settings.reminder_service import check_reminders, check_todo_reminders

async def main():
    await check_reminders()
    await check_todo_reminders()

if __name__ == "__main__":
    asyncio.run(main())

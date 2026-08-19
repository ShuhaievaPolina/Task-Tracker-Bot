import logging

import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router

from core.scheduler import scheduler
from jobs.reminder_jobs import send_remainder_simple_task

from database import create_db, delete_from_db, get_db

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()
dp.include_router(router)

async def handle_ping(request):
    return web.Response(text="The bot is running successfully")


async def main():
    bot = Bot(token=TOKEN)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    await create_db()

    all_task = await get_db()
    for task in all_task:

        if task["task_type"] == 'one_time':
            try:
                tz = ZoneInfo(task["time_zone"])
                now = datetime.now(tz)
                run_date = datetime.fromisoformat(task["run_datetime"])

                if run_date < now:
                    await delete_from_db(task["task_id"])
                    continue
                    
                scheduler.add_job(
                    send_remainder_simple_task,
                    trigger='date',             
                    run_date=run_date,          
                    args=[bot, task["user_id"], task["task_name"], task["task_id"]],
                    id=task["task_id"],
                    replace_existing=True 
                )
            except Exception as e:
                logger.error(f"Failed to restore the one-time task {task['task_name']}: {e}")


        elif task["task_type"] == 'recurring':
            scheduler.add_job(
                send_remainder_simple_task,
                trigger='cron',
                day_of_week=task["days_of_week"],
                hour=task["hours"],
                minute=task["minutes"],
                timezone=task["time_zone"],
                args=[bot, task["user_id"], task["task_name"]],
                id=task["task_id"],
                replace_existing=True 
            )

    logger.info(f"Tasks successfully restored from the database: {len(all_task)}")

    scheduler.start()

    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Dummy web server started on port {port}")

    logger.info("Start...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


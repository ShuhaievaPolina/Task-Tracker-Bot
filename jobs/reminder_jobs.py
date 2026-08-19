import asyncio
import logging
from aiogram import Bot

from database import delete_from_db, get_user_lang
from locales import get_text

logger = logging.getLogger(__name__)

async def send_remainder_simple_task(bot: Bot, chat_id: int, task_name: str, task_id: str = None):
    try:
        lang = await get_user_lang(chat_id)
        text = get_text(lang, "send_remainder", task_name=task_name)
        await bot.send_message(
            chat_id=chat_id , 
            text=text,
            parse_mode="HTML"
        )

        if task_id:
            await delete_from_db(task_id)

    except Exception as e:
        logger.error(f"Error sending reminder '{task_name}' to {chat_id}: {e}")

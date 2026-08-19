from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from locales import get_text

async def update_user_menu(bot: Bot, user_id: int, lang: str):
    commands = [
        BotCommand(command="start", description=get_text(lang,"menu_start") ),
        BotCommand(command="add", description=get_text(lang,"menu_add") ),
        BotCommand(command="delete", description=get_text(lang,"menu_delete") ),
        BotCommand(command="show_all_my_tasks", description=get_text(lang,"menu_show_all") ),
        BotCommand(command="update_language", description=get_text(lang,"menu_lang") )
    ]

    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(chat_id=user_id)
    )
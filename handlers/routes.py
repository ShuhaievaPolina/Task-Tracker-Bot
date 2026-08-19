from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import(
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from Tasks.simple import Task
from users.user_setting import User
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.scheduler import scheduler
from jobs.reminder_jobs import send_remainder_simple_task
from Tasks.delete_task import DeleteTask
from apscheduler.jobstores.base import JobLookupError

import math

from database import add_to_db, update_user_language, delete_from_db, get_user_lang, get_user_tasks_from_db
from locales import get_text


router = Router()

def get_week(lang: str):
    return [
        {"name": get_text(lang, "monday"), "callback": "opt_mon"},
        {"name": get_text(lang, "tuesday"), "callback": "opt_tue"},
        {"name": get_text(lang, "wednesday"), "callback": "opt_wed"},
        {"name": get_text(lang, "thursday"), "callback": "opt_thu"},
        {"name": get_text(lang, "friday"), "callback": "opt_fri"},
        {"name": get_text(lang, "saturday"), "callback": "opt_sat"},
        {"name": get_text(lang, "sunday"), "callback": "opt_sun"}
    ]



def get_inline_keyboard(special_button=None, buttons=None, selected_days=None):
    
    builder = InlineKeyboardBuilder()
    selected = selected_days if selected_days else []
      
    if buttons:
        for opt in buttons:
            text = f"✅{opt.get('name')}" if opt.get('callback') in selected else opt.get('name')
            callback_data = opt.get("callback")

            builder.button(text = text, callback_data = callback_data)

    if special_button:
        if isinstance(special_button, dict):
            special_button = [special_button]

        for opt in special_button:
            text = opt.get('name')
            callback_data = opt.get('callback')

            builder.button(text = text, callback_data = callback_data)


    sizes = []
    if buttons:
        full_rows = len(buttons)//3
        sizes.extend([3]*full_rows)

        remainder = len(buttons)%3
        if remainder > 0:
            sizes.append(remainder)

    if special_button:
        if isinstance(special_button, dict):
            sizes.extend([1])
        else:
            sizes.extend([1] * len(special_button))

    if sizes:
        builder.adjust(*sizes)
      

    return builder.as_markup()



@router.message(Command ("start"))
async def start(message: Message):
    user_id = message.from_user.id
    await update_user_language(user_id, language=message.from_user.language_code or "en")
    lang = await get_user_lang(user_id)
    text = get_text(lang, "start")
    await message.answer(text)



@router.message(Command("add"))
async def add_task(message: Message, state:FSMContext):
    lang = await get_user_lang(message.from_user.id)
    text = get_text(lang, "enter_name")
    await message.answer(text)
    await state.set_state(Task.task_name)



@router.message(Command("cancel"))
async def cancel_task(message: Message, state:FSMContext):
    await state.clear()
    lang = await get_user_lang(message.from_user.id)
    text = get_text(lang, "cancel")
    await message.answer(text)



@router.message(Task.task_name, F.text)
async def proccess_task_name(message: Message, state:FSMContext):
    await state.update_data(task_name=message.text)
    lang = await get_user_lang(message.from_user.id)
    text = get_text(lang, "enter_time")
    await message.answer(text)
    await state.set_state(Task.hours)



@router.message(Task.hours, F.text)
async def proccess_time(message: Message, state:FSMContext):
    time_text = message.text
    lang = await get_user_lang(message.from_user.id)

    if not ":" in time_text:
        text = get_text(lang, "enter_time_error_1")
        await message.answer(text)
        return

    time_digit = time_text.strip().split(":")

    if len(time_digit)!=2:
        text = get_text(lang, "enter_time_error_2")
        await message.answer(text)
        return

    hours = time_digit[0]
    minutes = time_digit[1]

    if not hours.isdigit() or not minutes.isdigit():
        text = get_text(lang, "enter_time_error_3")
        await message.answer(text)
        return

    if int(hours)<0 or int(hours)>24:
        text = get_text(lang, "enter_time_error_4", hours=hours)
        await message.answer(text)
        return

    if int(minutes)<0 or int(minutes)>59:
        text = get_text(lang, "enter_time_error_5", minutes=minutes)
        await message.answer(text)
        return

    await state.update_data(hours=int(hours))
    await state.set_state(Task.minutes)
    await state.update_data(minutes=int(minutes))

    button_1 = get_text(lang, "kiev_zone")
    button_2 = get_text(lang, "other_zone")
    buttons = [
        {"name": f"{button_1}", "callback": "kiev"},
        {"name": f"{button_2}", "callback": "input_time_zone"}
    ]

    text = get_text(lang, "enter_time_zone")
    await message.answer(text, reply_markup=get_inline_keyboard(buttons))
    await state.set_state(Task.time_zone)



@router.callback_query(Task.time_zone, F.data == "kiev")
async def proccess_kiev(callback: CallbackQuery, state:FSMContext, bot:Bot):
    await state.update_data(time_zone="Europe/Kiev")

    await callback.message.edit_reply_markup(reply_markup=None)

    lang = await get_user_lang(callback.from_user.id)
    button_1 = get_text(lang, "one_time")
    button_2 = get_text(lang, "recurring")
    buttons = [
        {"name": f"{button_1}", "callback": "one_time"},
        {"name": f"{button_2}", "callback": "recurring"}
    ]

    text = get_text(lang, "enter_type_remainder")
    await callback.message.answer(text, reply_markup=get_inline_keyboard(buttons))
    await state.set_state(Task.task_type)
    await callback.answer()




@router.callback_query(Task.time_zone, F.data == "input_time_zone")
async def process_input_time_zone_btn(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    lang = await get_user_lang(callback.from_user.id)
    text = get_text(lang, "enter_other_time_zone")
    await callback.message.answer(text)
    await callback.answer()



@router.message(Task.time_zone, F.text)
async def process_custom_time_zone_text(message: Message, state: FSMContext, bot: Bot):
    input_zone = message.text.strip()
    lang = await get_user_lang(message.from_user.id)

    try:
        user_tz = ZoneInfo(input_zone)

    except ZoneInfoNotFoundError:
        text = get_text(lang, "invalid_time_zone")
        await message.answer(text)
        return 

    except Exception as e:
        text = get_text(lang, "scheduler_error")
        await message.answer(text)
        return

    await state.update_data(time_zone=input_zone)

    button_1 = get_text(lang, "one_time")
    button_2 = get_text(lang, "recurring")
    buttons = [
        {"name": f"{button_1}", "callback": "one_time"},
        {"name": f"{button_2}", "callback": "recurring"}
    ]

    text = get_text(lang, "enter_type_remainder")
    await message.answer(text, reply_markup=get_inline_keyboard(buttons))
    await state.set_state(Task.task_type)




@router.callback_query(Task.task_type, F.data == "one_time")
async def proccess_task_type_one_time(callback: CallbackQuery, state:FSMContext, bot:Bot):
    await state.update_data(task_type='one_time')
    await callback.message.edit_reply_markup(reply_markup=None)

    lang = await get_user_lang(callback.from_user.id)
    
    data = await state.get_data()

    name = data["task_name"]
    hours = data["hours"]
    minutes = data["minutes"]
    time_zone = data["time_zone"]
    task_type = data["task_type"]

    user_id=callback.from_user.id
    task_id=f"{user_id}_{name}"

    try:
        user_tz = ZoneInfo(time_zone)
        now = datetime.now(user_tz)
        run_date = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        if run_date<now:
           run_date+=timedelta(days=1)

    except Exception as e:
        text = get_text(lang, "one_time_error")
        await callback.message.answer(text)
        await state.clear()
        await callback.answer()
        return

    scheduler.add_job(
        send_remainder_simple_task,
        trigger='date',
        run_date=run_date,
        args=[bot, user_id, name, task_id],
        id=task_id,
        replace_existing=True
    )

    run_datetime_str = run_date.isoformat()

    await add_to_db(task_id, user_id, name, run_datetime_str, hours, minutes, time_zone, task_type, None)

    formatted_date = run_date.strftime("%d.%m.%Y")

    text = get_text(lang, "message_one_time_remainder", name=name, formatted_date=formatted_date, hours=hours, minutes=minutes, time_zone=time_zone)
    await callback.message.answer(text, parse_mode="HTML")
    
    await callback.answer()
    await state.clear()



@router.callback_query(Task.task_type, F.data == "recurring")
async def proccess_task_type_recurring(callback: CallbackQuery, state: FSMContext):
    await state.update_data(task_type='recurring')
    await callback.message.edit_reply_markup(reply_markup=None)

    lang = await get_user_lang(callback.from_user.id)
    text_but = get_text(lang, "buttom_enter_day_of_week")

    spec_but = {"name":f"{text_but}", "callback": "end" }


    await state.set_state(Task.days_of_week)
    text = get_text(lang, "enter_days_of_week")
    await callback.message.answer(text, reply_markup=get_inline_keyboard(spec_but,get_week(lang)))
    callback.answer()


@router.callback_query(Task.days_of_week, F.data.startswith("opt_"))
async def proccess_days_of_week_choice(callback: CallbackQuery, state: FSMContext):
    
    callback_day = callback.data

    data = await state.get_data()
    sel_days_of_week = data.get("selected_days", [])

    lang = await get_user_lang(callback.from_user.id)

    if callback_day in sel_days_of_week:
        sel_days_of_week.remove(callback_day)
    else:
        sel_days_of_week.append(callback_day)

    await state.update_data(selected_days=sel_days_of_week)

    text_but = get_text(lang, "buttom_enter_day_of_week")
    spec_but = {"name":f"{text_but}", "callback": "end" }

    try:
        await callback.message.edit_reply_markup(reply_markup=get_inline_keyboard(special_button=spec_but, buttons=get_week(lang), selected_days=sel_days_of_week))
    except Exception:
        pass
    
    await callback.answer()



    @router.callback_query(Task.days_of_week, F.data == "end")
    async def confirm_days_of_week(callback: CallbackQuery, state: FSMContext, bot:Bot):

        lang = await get_user_lang(callback.from_user.id)

        data = await state.get_data()
        sel_days_of_week = data.get("selected_days", [])

        if not sel_days_of_week:
            text = get_text(lang, "enter_days_of_week_error")
            await callback.answer(text, show_alert=True)
            return

        else:
            human_days = []
            cron_days = []

            for opt in sel_days_of_week:
               cron_days.append(opt.split("_")[1])

               for day in get_week(lang):
                   if day.get('callback') == opt:
                       human_days.append(day.get('name'))
                       break

            str_name_day = ", ".join(human_days)
            cron_str = ",".join(cron_days)

            await state.update_data(days_of_week=str_name_day)
            data = await state.get_data()

            name = data["task_name"]
            # run_time = data["run_time"]
            # hours = run_time.strftime("%H")
            # minutes = run_time.strftime("%M")
            hours = data["hours"]
            minutes = data["minutes"]
            time_zone = data["time_zone"]
            task_type = data["task_type"]

            user_id=callback.from_user.id
            task_id=f"{user_id}_{name}"

            scheduler.add_job(
                send_remainder_simple_task,
                trigger='cron',
                day_of_week=cron_str,
                hour=hours,
                minute=minutes,
                timezone=time_zone,
                args=[bot, user_id, name],
                id = task_id,
                replace_existing=True
            )

            await add_to_db(task_id, user_id, name, None, hours, minutes, time_zone, task_type, cron_str)

            text = get_text(lang, "message_reccuring_remainder", name=name, hours=hours, minutes=minutes, time_zone=time_zone, str_name_day=str_name_day)
            await callback.message.answer(text, parse_mode="HTML")
            # await callback.message.answer(
            #     f"<b>{name}</b>\n\n"
            #     f"Время: {hours:02d}:{minutes:02d}\n"
            #     f"Часовой пояс: {time_zone}\n"
            #     f"Тип напоминания: Переодическое\n"
            #     f"Повторять в {str_name_day}", 
            #     parse_mode="HTML"
            # )

            await callback.answer()
            await state.clear()




@router.message(Command("show_all_my_tasks"))
async def show_all_user_tasks(message: Message):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    user_tasks = await get_user_tasks_from_db(user_id)

    if not user_tasks:
        text = get_text(lang, "no_reminder")
        await message.answer(text)
        return

    text=get_text(lang,"all_remainder")

    for task in user_tasks:
        name = task["task_name"]
        hours = task["hours"]
        minutes = task["minutes"]
        time_zone = task["time_zone"]
        str_days = task["days_of_week"]

        if str_days:
            days = str_days.split(',')
            res=[]

            for day in days:
                for opt in get_week(lang):
                    if day == opt.get('callback').split('_')[1]:
                        res.append(opt.get('name'))
                        break

            str_res = ", ".join(res)
            days_text = get_text(lang, "all_remainder_message", str_res=str_res)

        else:
            days_text = ""

        text += get_text(lang, "all_remainder_message_text", name=name, hours=hours, minutes=minutes, days_text=days_text, time_zone=time_zone)

    await message.answer(text, parse_mode="HTML")



@router.message(Command("delete"))
async def delete_simple_task(message: Message, state:FSMContext):
    lang = await get_user_lang(message.from_user.id)
    text = get_text(lang, "enter_name")
    await message.answer(text)
    await state.set_state(DeleteTask.name)



@router.message(DeleteTask.name, F.text)
async def procces_delete_simple_task(message: Message, state:FSMContext):
    task_name=message.text.strip().lower()
    user_id=message.from_user.id
    lang = await get_user_lang(user_id)

    user_tasks = await get_user_tasks_from_db(user_id)

    task_id = next((task["task_id"] for task in user_tasks if task["task_name"].strip().lower() == task_name), None)

    if not task_id:
        text = get_text(lang, "remainder_not_found_error",task_name=task_name)
        await message.answer(text, parse_mode="HTML")
        await state.clear()
        return

    try:
        scheduler.remove_job(task_id)
        await state.update_data(name=task_name)
    except JobLookupError:
        pass
    except Exception:
        text = get_text(lang, "scheduler_error")
        await message.answer(text)

    try:
        await delete_from_db(task_id)
        text = get_text(lang, "delete_remainder",task_name=task_name)
        await message.answer(text, parse_mode="HTML")
    except Exception:
        text = get_text(lang, "delete_remainder_error")
        await message.answer(text)

    await state.clear()


@router.message(Command("update_language"))
async def update_language(message: Message, state: FSMContext):

    lang = await get_user_lang(message.from_user.id)
    await state.set_state(User.lang)

    buttons = [
        {"name": f"English", "callback": "en"},
        {"name": f"Русский", "callback": "ru"},
        {"name": f"Українська", "callback": "uk"},
    ]

    text = get_text(lang, "enter_change_lang")
    await message.answer(text, reply_markup=get_inline_keyboard(buttons))
    

@router.callback_query(User.lang)
async def set_new_language(callback: CallbackQuery, state:FSMContext):
    set_lang = callback.data
    await update_user_language(callback.from_user.id, set_lang)
    lang = await get_user_lang(callback.from_user.id)
    await state.update_data(lang = set_lang)
    text = get_text(lang,"change_lang")
    await callback.message.answer(text)

    await callback.answer()
    await state.clear()



@router.message()
async def default_mess(message: Message):
    lang = await get_user_lang(message.from_user.id)
    text = get_text(lang, "default_mess")
    await message.answer(text)
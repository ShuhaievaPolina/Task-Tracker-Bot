import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def create_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                language TEXT DEFAULT 'en'
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                task_id TEXT PRIMARY KEY,
                user_id BIGINT,
                task_name TEXT,
                run_datetime TEXT,
                hours INTEGER,
                minutes INTEGER,
                time_zone TEXT,
                task_type TEXT,
                days_of_week TEXT
            )
        """)
    finally:
        await conn.close()

# COMAND FOR TASKS TABLE

async def add_to_db(task_id: str, user_id: int, task_name: str, run_datetime: str, hours: int, minute: int, time_zone: str, task_type: str, days_of_week: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO tasks (task_id, user_id, task_name, run_datetime, hours, minutes, time_zone, task_type, days_of_week) 
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (task_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                task_name = EXCLUDED.task_name,
                run_datetime = EXCLUDED.run_datetime,
                hours = EXCLUDED.hours,
                minutes = EXCLUDED.minutes,
                time_zone = EXCLUDED.time_zone,
                task_type = EXCLUDED.task_type,
                days_of_week = EXCLUDED.days_of_week
        """, task_id, user_id, task_name, run_datetime, hours, minute, time_zone, task_type, days_of_week)
    finally:
        await conn.close()

async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetch("SELECT * FROM tasks")
        return [dict(res) for res in result]
    finally:
        await conn.close()

async def get_user_tasks_from_db(user_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetch("SELECT * FROM tasks WHERE user_id=$1", user_id)
        return [dict(res) for res in result]
    finally:
        await conn.close()

async def delete_from_db(task_id: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM tasks WHERE task_id=$1", task_id)
    finally:
        await conn.close()

# COMAND FOR USERS TABLE

async def update_user_language(user_id: int, language: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO users (user_id, language) VALUES($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language
        """, user_id, language)
    finally:
        await conn.close()

async def get_user_lang(user_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        res = await conn.fetchrow("SELECT language FROM users WHERE user_id=$1", user_id)
        return res['language'] if res else 'en'
    finally:
        await conn.close()



# import aiosqlite
# DB_NAME="Task.sql"

# async def create_db():
#     async with aiosqlite.connect(DB_NAME) as db:

#         await db.execute("""
#             CREATE TABLE IF NOT EXISTS users(
#                 user_id INTEGER PRIMARY KEY,
#                 language TEXT DEFAULT 'eng'
#             )
#         """)

#         await db.execute("""
#             CREATE TABLE IF NOT EXISTS tasks(
#                 task_id TEXT PRIMARY KEY,
#                 user_id INTEGER,
#                 task_name TEXT,
#                 run_datetime TEXT,
#                 hours INTEGER,
#                 minutes INTEGER,
#                 time_zone TEXT,
#                 task_type TEXT,
#                 days_of_week TEXT
#             )
#         """)
#         await db.commit()


# """
# COMAND FOR TASKS TABLE
# """

# async def add_to_db(task_id: str,user_id: int, task_name: str, run_datetime: str, hours: int, minute: int, time_zone: str, task_type: str, days_of_week: str):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute("INSERT OR REPLACE INTO tasks (task_id, user_id, task_name, run_datetime, hours, minutes, time_zone, task_type, days_of_week) VALUES(?,?,?,?,?,?,?,?,?)",(task_id, user_id, task_name, run_datetime, hours, minute, time_zone, task_type, days_of_week))
#         await db.commit()



# async def get_db():
#     async with aiosqlite.connect(DB_NAME) as db:
#         db.row_factory=aiosqlite.Row
#         async with db.execute("SELECT * FROM tasks") as cursor:
#             result = await cursor.fetchall()
#             return [dict(res) for res in result]



# async def get_user_tasks_from_db(user_id: int):
#     async with aiosqlite.connect(DB_NAME) as db:
#         db.row_factory=aiosqlite.Row
#         async with db.execute("SELECT * FROM tasks WHERE user_id=?",(user_id,)) as cursor:
#             result = await cursor.fetchall()
#             return [dict(res) for res in result]



# async def delete_from_db(task_id: str):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
#         await db.commit()


# """
# COMAND FOR USERS TABLE
# """

# async def update_user_language(user_id: int, language: str):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES(?,?)",(user_id, language))
#         await db.commit()



# async def get_user_lang(user_id: int):
#     async with aiosqlite.connect(DB_NAME) as db:
#         async with db.execute("SELECT language FROM users WHERE user_id=?",(user_id,)) as cursor:
#             res = await cursor.fetchone()
#             return res[0] if res else 'en'
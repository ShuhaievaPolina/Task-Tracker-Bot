# Task Tracker Telegram Bot

An asynchronous Telegram bot for convenient management of personal tasks and reminders. The bot allows users to create both one-time and recurring notifications, perfectly handling different time zones.

## Features

* **Multilingual Support:** Supports English, Russian, and Ukrainian languages (user preferences are saved in the database).
* **Smart Reminders:** Create one-time tasks for a specific date and recurring tasks based on days of the week.
* **Time Zones:** Accurate time processing with support for custom time zones (using the `zoneinfo` library).
* **Task Management:** View the list of all active tasks, edit their scheduled time, and delete them.
* **Reliability:** All data is stored in PostgreSQL, ensuring that reminders are never lost, even during server restarts.

## Tech Stack

* **Language:** Python 3
* **Framework:** aiogram 3.x (with FSM)
* **Database:** PostgreSQL + `asyncpg`
* **Scheduler:** APScheduler
* **Logging:** Standard `logging` module

## Local Setup (for developers)

1. Clone the repository:
   git clone https://github.com/ShuhaievaPolina/Task-Tracker-Bot.git

2. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Create an `.env` file in the project root and add your keys:
   BOT_TOKEN=your_token_from_botfather
   DATABASE_URL=your_postgresql_connection_string

5. Run the bot:
   python Task_Tracker_Bot.py

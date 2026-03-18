# Telegram Schedule Tracking Agent

A Telegram-based schedule assistant that records, updates, and lists schedules through natural language.

This repository is safe to publish:
- Real API keys are **not included**
- `.env` is ignored by git
- Use `.env.example` to create your own local `.env`

## Features
- Natural language scheduling in English and Chinese
- Add, update, delete, and list schedules from Telegram
- Two schedule groups:
  - `Submission`
  - `Upcoming Schedule`
- Course number labels for submissions
- Natural-language editing for course number, category, recurrence, location, time, and importance
- Bulk updates, for example:
  - `Update all from E1 to E6 to course number CC0006`
- Image-to-schedule extraction with confirmation before saving
- Recurring events
- Reminders with inline actions:
  - `Done`
  - `Snooze 10m / 30m / 1h`
  - `Reschedule`
- History for expired schedules
- Safe clear-all flow with confirmation

## Default behavior
- Default timezone: `Asia/Singapore`
- Default category: `upcoming`
- Default type: `NORMAL`
- Default recurrence: `none`
- Default course number: `none`
- Default location: `none`
- Default duration: `1 hour` if end time is not provided

## Setup
1. Install Python 3.10 or newer.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the env template:

```powershell
Copy-Item .env.example .env
```

4. Fill in your own values in `.env`.

## Required environment variables
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `OPENAI_MODEL`
- `TIMEZONE`
- `COMMAND_POLL_SECONDS`
- `REMINDER_SCAN_SECONDS`
- `CLEANUP_HOUR_LOCAL`

## Run locally
Start the bot:

```powershell
py -3 src/schedule_agent.py
```

One-time polling:

```powershell
py -3 src/schedule_agent.py --commands-once
```

## Telegram commands
- `/list`
- `/history`
- `/history <days>`
- `/confirm`
- `/confirm_clear_all`
- `/cancel`
- `/status`
- `/help`

## Example messages
- `I have a meeting tomorrow at 2pm with Alex`
- `Add CS101 assignment submission due Friday 11:59pm`
- `Set course number to MA1521 for E12`
- `Change E12 recurring to daily`
- `Update all from E1 to E6 to course number CC0006`
- `Clear all schedules`

## Railway deployment
This project includes:
- `railway.toml`
- `.railwayignore`

For Railway:
1. Create a service
2. Add environment variables from `.env.example`
3. Mount a persistent volume at `/app/data`
4. Deploy

## Security
- Do **not** commit `.env`
- Do **not** paste real API keys into source files
- Rotate keys if they were ever exposed

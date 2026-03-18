# Project Note

This bot is designed to act as a personal schedule assistant on Telegram.

## What it does
- Understands natural language schedule requests
- Stores schedules and recurring events
- Separates items into `Submission` and `Upcoming Schedule`
- Labels submissions with a course number
- Lets you edit single schedules or multiple schedules at once
- Extracts schedule details from images, then asks for confirmation before saving
- Sends reminders and keeps short-term expired history

## How to use it
- Send schedule text naturally:
  - `Add CS101 assignment submission due Friday 11:59pm`
- Ask for your schedule:
  - `/list`
- Edit an item:
  - `Set course number to CC0006 for E3`
- Edit multiple items:
  - `Update all from E1 to E6 to course number CC0006`
- Clear everything safely:
  - `Clear all schedules`
  - then confirm with `confirm clear all`

## Before publishing
- Create your own `.env` from `.env.example`
- Keep `.env` private
- Review the repo once before pushing

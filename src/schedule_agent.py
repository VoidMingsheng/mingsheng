
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import parser as date_parser
from dateutil.rrule import DAILY, MONTHLY, WEEKLY, FR, MO, SA, SU, TH, TU, WE, rrule
from dotenv import load_dotenv
from openai import OpenAI
from zoneinfo import ZoneInfo

WEEKDAY_MAP = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_iso_utc(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_local_iso_to_utc(text: str, tz: ZoneInfo) -> datetime | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def parse_local_flexible_to_utc(text: str, tz: ZoneInfo) -> datetime | None:
    parsed = parse_local_iso_to_utc(text, tz)
    if parsed is not None:
        return parsed
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        dt = date_parser.parse(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def fmt_local(utc_text: str, tz: ZoneInfo) -> str:
    return parse_iso_utc(utc_text).astimezone(tz).strftime("%Y-%m-%d %I:%M %p")


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def to_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return None


def normalize_category(value: Any, *context: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"submission", "submissions", "deadline", "deadlines", "due"}:
        return "submission"
    if raw in {"upcoming", "schedule", "event", "events"}:
        return "upcoming"

    merged = " ".join(str(item or "").strip().lower() for item in context if str(item or "").strip())
    submission_terms = [
        "submission",
        "submit",
        "submitted",
        "deadline",
        "due",
        "deliverable",
        "assignment",
        "homework",
        "project due",
        "report due",
        "ddl",
        "鎴",
        "鎻愪氦",
        "浣滀笟",
        "鍔熻",
        "浜や粯",
    ]
    return "submission" if any(term in merged for term in submission_terms) else "upcoming"


def category_label(value: str) -> str:
    return "SUBMISSION" if normalize_category(value) == "submission" else "UPCOMING"


def normalize_course_number(value: Any, *context: Any) -> str:
    raw = str(value or "").strip().rstrip(".,;:)")
    if raw:
        lowered = raw.lower()
        if lowered in {"none", "n/a", "na", "null", "nil", "-", "remove", "clear", "empty"}:
            return "none"
        return re.sub(r"\s+", "", raw).upper()[:40] or "none"

    merged = " ".join(str(item or "").strip() for item in context if str(item or "").strip())
    if not merged:
        return "none"
    match = re.search(r"\b([A-Za-z]{2,8}\s*[-/]?\s*\d{2,6}[A-Za-z]?)\b", merged)
    if not match:
        return "none"
    return re.sub(r"\s+", "", match.group(1)).upper()[:40] or "none"


def should_show_course_number(category: str, course_number: str) -> bool:
    return normalize_category(category) == "submission" or normalize_course_number(course_number) != "none"


def format_course_line(category: str, course_number: str, prefix: str = "Course") -> str:
    normalized = normalize_course_number(course_number)
    if not should_show_course_number(category, normalized):
        return ""
    return f"{prefix}: {normalized}"


@dataclass
class Config:
    openai_api_key: str
    openai_model: str
    telegram_bot_token: str
    telegram_chat_id: str
    timezone_name: str
    command_poll_seconds: int
    reminder_scan_seconds: int
    cleanup_hour_local: int


@dataclass
class PartialConfig:
    telegram_bot_token: str
    telegram_chat_id: str


@dataclass
class Event:
    id: int
    title: str
    description: str
    location: str
    category: str
    course_number: str
    start_at_utc: str
    end_at_utc: str
    timezone_name: str
    is_important: bool
    is_recurring: bool
    recurrence_rule: dict[str, Any]
    status: str
    source_text: str

    @property
    def start_dt_utc(self) -> datetime:
        return parse_iso_utc(self.start_at_utc)

    @property
    def end_dt_utc(self) -> datetime:
        return parse_iso_utc(self.end_at_utc)


@dataclass
class Occurrence:
    event_id: int
    title: str
    start_at_utc: datetime
    end_at_utc: datetime
    is_important: bool
    source_occurrence_start_utc: datetime


def load_config() -> Config:
    load_dotenv()
    return Config(
        openai_api_key=require_env("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        telegram_bot_token=require_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=require_env("TELEGRAM_CHAT_ID"),
        timezone_name=os.getenv("TIMEZONE", "Asia/Singapore").strip(),
        command_poll_seconds=int(os.getenv("COMMAND_POLL_SECONDS", "20")),
        reminder_scan_seconds=int(os.getenv("REMINDER_SCAN_SECONDS", "60")),
        cleanup_hour_local=int(os.getenv("CLEANUP_HOUR_LOCAL", "3")),
    )


def load_partial_config() -> PartialConfig:
    load_dotenv()
    return PartialConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    )


class StateStore:
    def __init__(self, db_path: str = "data/schedule_state.db") -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT 'none',
                category TEXT NOT NULL DEFAULT 'upcoming',
                course_number TEXT NOT NULL DEFAULT 'none',
                start_at_utc TEXT NOT NULL,
                end_at_utc TEXT NOT NULL,
                timezone_name TEXT NOT NULL,
                is_important INTEGER NOT NULL DEFAULT 0,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                recurrence_rule TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'active',
                source_text TEXT NOT NULL DEFAULT '',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            )
            """
        )
        event_cols = {str(row["name"]) for row in self.conn.execute("PRAGMA table_info(events)").fetchall()}
        if "location" not in event_cols:
            self.conn.execute("ALTER TABLE events ADD COLUMN location TEXT NOT NULL DEFAULT 'none'")
        if "category" not in event_cols:
            self.conn.execute("ALTER TABLE events ADD COLUMN category TEXT NOT NULL DEFAULT 'upcoming'")
        if "course_number" not in event_cols:
            self.conn.execute("ALTER TABLE events ADD COLUMN course_number TEXT NOT NULL DEFAULT 'none'")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS occurrence_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                occurrence_start_utc TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                rescheduled_start_utc TEXT,
                rescheduled_end_utc TEXT,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                UNIQUE(event_id, occurrence_start_utc)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminder_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                occurrence_start_utc TEXT NOT NULL,
                offset_minutes INTEGER NOT NULL,
                sent_at_utc TEXT NOT NULL,
                UNIQUE(event_id, occurrence_start_utc, offset_minutes)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_tokens (
                token TEXT PRIMARY KEY,
                event_id INTEGER NOT NULL,
                occurrence_start_utc TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snoozed_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                occurrence_start_utc TEXT NOT NULL,
                due_at_utc TEXT NOT NULL,
                sent_at_utc TEXT,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kv (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        try:
            recurrence = json.loads(row["recurrence_rule"] or "{}")
        except Exception:
            recurrence = {}
        return Event(
            id=int(row["id"]),
            title=row["title"],
            description=row["description"],
            location=str(row["location"] if "location" in row.keys() else "none") or "none",
            category=str(row["category"] if "category" in row.keys() else "upcoming") or "upcoming",
            course_number=str(row["course_number"] if "course_number" in row.keys() else "none") or "none",
            start_at_utc=row["start_at_utc"],
            end_at_utc=row["end_at_utc"],
            timezone_name=row["timezone_name"],
            is_important=bool(row["is_important"]),
            is_recurring=bool(row["is_recurring"]),
            recurrence_rule=recurrence,
            status=row["status"],
            source_text=row["source_text"],
        )

    def get(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
        return row["v"] if row else default

    def set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO kv(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v",
            (key, value),
        )
        self.conn.commit()

    def delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM kv WHERE k = ?", (key,))
        self.conn.commit()

    def create_event(
        self,
        *,
        title: str,
        description: str,
        location: str,
        category: str,
        course_number: str,
        start_at_utc: str,
        end_at_utc: str,
        timezone_name: str,
        is_important: bool,
        is_recurring: bool,
        recurrence_rule: dict[str, Any],
        source_text: str,
    ) -> Event:
        now_iso = utc_now().isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO events(
                title, description, location, category, course_number, start_at_utc, end_at_utc, timezone_name,
                is_important, is_recurring, recurrence_rule, status, source_text, created_at_utc, updated_at_utc
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """,
            (
                title[:200],
                description[:800],
                (location.strip() or "none")[:180],
                normalize_category(category),
                normalize_course_number(course_number),
                start_at_utc,
                end_at_utc,
                timezone_name,
                1 if is_important else 0,
                1 if is_recurring else 0,
                json.dumps(recurrence_rule),
                source_text[:1200],
                now_iso,
                now_iso,
            ),
        )
        self.conn.commit()
        return self.get_event(int(cur.lastrowid))

    def get_event(self, event_id: int) -> Event:
        row = self.conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise ValueError(f"Event {event_id} not found")
        return self._row_to_event(row)

    def list_active_events(self) -> list[Event]:
        rows = self.conn.execute("SELECT * FROM events WHERE status = 'active' ORDER BY start_at_utc ASC").fetchall()
        return [self._row_to_event(r) for r in rows]

    def search_active_events(self, query: str, limit: int = 20) -> list[Event]:
        query = query.strip()
        if not query:
            return []
        id_match = re.search(r"\bE(\d+)\b", query.upper())
        if id_match:
            eid = int(id_match.group(1))
            rows = self.conn.execute("SELECT * FROM events WHERE id = ? AND status = 'active'", (eid,)).fetchall()
            return [self._row_to_event(r) for r in rows]
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM events
            WHERE status = 'active' AND (title LIKE ? OR description LIKE ? OR location LIKE ? OR category LIKE ? OR course_number LIKE ? OR source_text LIKE ?)
            ORDER BY start_at_utc ASC
            LIMIT ?
            """,
            (like, like, like, like, like, like, limit),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def update_event_fields(self, event_id: int, fields: dict[str, Any]) -> Event:
        if not fields:
            return self.get_event(event_id)
        allowed = {
            "title",
            "description",
            "location",
            "category",
            "course_number",
            "start_at_utc",
            "end_at_utc",
            "is_important",
            "is_recurring",
            "recurrence_rule",
            "status",
        }
        parts: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "recurrence_rule":
                parts.append("recurrence_rule = ?")
                values.append(json.dumps(value))
            elif key in {"is_important", "is_recurring"}:
                parts.append(f"{key} = ?")
                values.append(1 if bool(value) else 0)
            elif key == "category":
                parts.append("category = ?")
                values.append(normalize_category(value))
            elif key == "course_number":
                parts.append("course_number = ?")
                values.append(normalize_course_number(value))
            else:
                parts.append(f"{key} = ?")
                values.append(value)
        if not parts:
            return self.get_event(event_id)
        parts.append("updated_at_utc = ?")
        values.append(utc_now().isoformat())
        values.append(event_id)
        self.conn.execute(f"UPDATE events SET {', '.join(parts)} WHERE id = ?", tuple(values))
        self.conn.commit()
        return self.get_event(event_id)
    def delete_event(self, event_id: int) -> None:
        self.update_event_fields(event_id, {"status": "deleted"})

    def set_occurrence_override(
        self,
        *,
        event_id: int,
        occurrence_start_utc: str,
        status: str,
        rescheduled_start_utc: str | None = None,
        rescheduled_end_utc: str | None = None,
    ) -> None:
        now_iso = utc_now().isoformat()
        self.conn.execute(
            """
            INSERT INTO occurrence_overrides(
                event_id, occurrence_start_utc, status, rescheduled_start_utc, rescheduled_end_utc, created_at_utc, updated_at_utc
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, occurrence_start_utc) DO UPDATE SET
                status = excluded.status,
                rescheduled_start_utc = excluded.rescheduled_start_utc,
                rescheduled_end_utc = excluded.rescheduled_end_utc,
                updated_at_utc = excluded.updated_at_utc
            """,
            (
                event_id,
                occurrence_start_utc,
                status,
                rescheduled_start_utc,
                rescheduled_end_utc,
                now_iso,
                now_iso,
            ),
        )
        self.conn.commit()

    def get_overrides_for_event(self, event_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM occurrence_overrides WHERE event_id = ? ORDER BY occurrence_start_utc ASC",
            (event_id,),
        ).fetchall()

    def mark_reminder_sent(self, event_id: int, occurrence_start_utc: str, offset_minutes: int) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO reminder_log(event_id, occurrence_start_utc, offset_minutes, sent_at_utc) VALUES(?, ?, ?, ?)",
                (event_id, occurrence_start_utc, offset_minutes, utc_now().isoformat()),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def ensure_action_token(self, event_id: int, occurrence_start_utc: str) -> str:
        token = hashlib.sha1(f"{event_id}:{occurrence_start_utc}".encode("utf-8")).hexdigest()[:16]
        self.conn.execute(
            "INSERT OR IGNORE INTO action_tokens(token, event_id, occurrence_start_utc, created_at_utc) VALUES(?, ?, ?, ?)",
            (token, event_id, occurrence_start_utc, utc_now().isoformat()),
        )
        self.conn.commit()
        return token

    def get_action_token(self, token: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM action_tokens WHERE token = ?", (token,)).fetchone()

    def create_snooze(self, event_id: int, occurrence_start_utc: str, due_at_utc: str) -> None:
        self.conn.execute(
            "INSERT INTO snoozed_reminders(event_id, occurrence_start_utc, due_at_utc, sent_at_utc, created_at_utc) VALUES(?, ?, ?, NULL, ?)",
            (event_id, occurrence_start_utc, due_at_utc, utc_now().isoformat()),
        )
        self.conn.commit()

    def pop_due_snoozes(self, now_utc_iso: str) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            "SELECT * FROM snoozed_reminders WHERE sent_at_utc IS NULL AND due_at_utc <= ? ORDER BY due_at_utc ASC",
            (now_utc_iso,),
        ).fetchall()
        if not rows:
            return []
        ids = [int(r["id"]) for r in rows]
        placeholders = ",".join("?" for _ in ids)
        params: list[Any] = [utc_now().isoformat()] + ids
        self.conn.execute(f"UPDATE snoozed_reminders SET sent_at_utc = ? WHERE id IN ({placeholders})", tuple(params))
        self.conn.commit()
        return rows

    def cleanup_history(self, cutoff_utc: datetime) -> None:
        cutoff_iso = cutoff_utc.isoformat()
        self.conn.execute("DELETE FROM events WHERE is_recurring = 0 AND end_at_utc < ?", (cutoff_iso,))
        self.conn.execute("DELETE FROM occurrence_overrides WHERE occurrence_start_utc < ?", (cutoff_iso,))
        self.conn.execute("DELETE FROM reminder_log WHERE occurrence_start_utc < ?", (cutoff_iso,))
        self.conn.execute("DELETE FROM action_tokens WHERE occurrence_start_utc < ? OR created_at_utc < ?", (cutoff_iso, cutoff_iso))
        self.conn.execute("DELETE FROM snoozed_reminders WHERE due_at_utc < ? OR created_at_utc < ?", (cutoff_iso, cutoff_iso))
        self.conn.commit()

    def schedule_data_counts(self) -> dict[str, int]:
        event_row = self.conn.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_events,
                COUNT(*) AS total_events
            FROM events
            """
        ).fetchone()
        return {
            "active_events": int((event_row["active_events"] if event_row and event_row["active_events"] is not None else 0) or 0),
            "total_events": int((event_row["total_events"] if event_row and event_row["total_events"] is not None else 0) or 0),
            "occurrence_overrides": int(self.conn.execute("SELECT COUNT(*) AS c FROM occurrence_overrides").fetchone()["c"] or 0),
            "reminder_logs": int(self.conn.execute("SELECT COUNT(*) AS c FROM reminder_log").fetchone()["c"] or 0),
            "snoozed_reminders": int(self.conn.execute("SELECT COUNT(*) AS c FROM snoozed_reminders").fetchone()["c"] or 0),
        }

    def clear_all_schedule_data(self) -> dict[str, int]:
        counts = self.schedule_data_counts()
        self.conn.execute("DELETE FROM events")
        self.conn.execute("DELETE FROM occurrence_overrides")
        self.conn.execute("DELETE FROM reminder_log")
        self.conn.execute("DELETE FROM action_tokens")
        self.conn.execute("DELETE FROM snoozed_reminders")
        self.conn.execute("DELETE FROM kv WHERE k <> 'telegram_offset'")
        self.conn.commit()
        return counts


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.chat_id = str(chat_id)
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{bot_token}"

    def send_message(self, text: str, reply_markup: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text[:3900],
            "disable_web_page_preview": True,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        resp = requests.post(f"{self.base_url}/sendMessage", json=payload, timeout=20)
        resp.raise_for_status()

    def get_updates(self, offset: int | None = None, timeout_sec: int = 10) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": timeout_sec}
        if offset is not None:
            params["offset"] = offset
        resp = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=timeout_sec + 5)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            return []
        return data.get("result", [])

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> None:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text[:180]
        requests.post(f"{self.base_url}/answerCallbackQuery", json=payload, timeout=10).raise_for_status()

    def edit_reply_markup(self, chat_id: str, message_id: int, reply_markup: dict[str, Any] | None) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        requests.post(f"{self.base_url}/editMessageReplyMarkup", json=payload, timeout=10).raise_for_status()

    def get_file_path(self, file_id: str) -> str:
        resp = requests.get(f"{self.base_url}/getFile", params={"file_id": file_id}, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("ok"):
            raise RuntimeError("Telegram getFile failed")
        result = payload.get("result") or {}
        file_path = str(result.get("file_path", "")).strip()
        if not file_path:
            raise RuntimeError("Telegram file path missing")
        return file_path

    def download_file_bytes(self, file_path: str) -> bytes:
        resp = requests.get(f"{self.file_base_url}/{file_path.lstrip('/')}", timeout=30)
        resp.raise_for_status()
        return resp.content


class Analyzer:
    def __init__(self, config: Config) -> None:
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model

    def interpret_message(self, *, text: str, now_local_iso: str, tz_name: str, sample_events: list[dict[str, Any]]) -> dict[str, Any]:
        system = (
            "You convert English and Chinese schedule messages into strict JSON. "
            "Understand relative dates and times from now_local_iso. "
            "Default values unless explicitly stated: is_important=false, is_recurring=false, location='none', category='upcoming', course_number='none'. "
            "Allowed intents: create, list_upcoming, list_history, update, delete, clear_all, mark_important, mark_normal, help, unknown. "
            "Return JSON only."
        )
        schema = {
            "intent": "create|list_upcoming|list_history|update|delete|clear_all|mark_important|mark_normal|help|unknown",
            "target_query": "string",
            "history_days": "integer optional",
            "create": {
                "title": "string",
                "description": "string",
                "location": "string",
                "category": "submission|upcoming",
                "course_number": "string",
                "start_local": "ISO local or empty",
                "end_local": "ISO local or empty",
                "is_important": "true/false",
                "is_recurring": "true/false",
                "recurrence": {
                    "freq": "none|daily|weekly|monthly|weekdays|every_n_weeks",
                    "interval": "integer",
                    "byweekday": [0, 1, 2, 3, 4, 5, 6],
                    "end_type": "never|count|until",
                    "count": "integer or null",
                    "until_local": "ISO local or empty",
                },
            },
            "changes": {
                "title": "string or empty",
                "description": "string or empty",
                "location": "string or empty",
                "category": "submission|upcoming or empty",
                "course_number": "string or empty",
                "start_local": "ISO local or empty",
                "end_local": "ISO local or empty",
                "duration_minutes": "integer or null",
                "set_recurring": "true|false|null",
                "recurrence": {
                    "freq": "none|daily|weekly|monthly|weekdays|every_n_weeks",
                    "interval": "integer",
                    "byweekday": [0, 1, 2, 3, 4, 5, 6],
                    "end_type": "never|count|until",
                    "count": "integer or null",
                    "until_local": "ISO local or empty",
                },
            },
        }
        payload = {
            "now_local_iso": now_local_iso,
            "timezone": tz_name,
            "message": text,
            "sample_upcoming_events": sample_events,
            "schema": schema,
        }
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def parse_datetime_message(self, *, text: str, now_local_iso: str, tz_name: str) -> dict[str, str]:
        system = "Extract datetime in JSON. Output fields start_local and end_local in ISO local format, or empty strings."
        payload = {
            "now_local_iso": now_local_iso,
            "timezone": tz_name,
            "message": text,
            "schema": {"start_local": "", "end_local": ""},
        }
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"start_local": "", "end_local": ""}
        if not isinstance(parsed, dict):
            return {"start_local": "", "end_local": ""}
        return {
            "start_local": str(parsed.get("start_local", "")).strip(),
            "end_local": str(parsed.get("end_local", "")).strip(),
        }

    def extract_schedules_from_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        now_local_iso: str,
        tz_name: str,
        caption: str,
    ) -> dict[str, Any]:
        system = (
            "You extract schedule items from an image (screenshot, calendar, chat, poster, notes) plus optional caption. "
            "Return strict JSON only. "
            "Default values: is_important=false, is_recurring=false, category='upcoming', course_number='none' unless explicitly stated in image or caption. "
            "If end time is unknown, leave end_local empty. "
            "Use ISO local datetime format without timezone suffix."
        )
        schema = {
            "events": [
                {
                    "title": "string",
                    "description": "string",
                    "location": "string",
                    "category": "submission|upcoming",
                    "course_number": "string",
                    "start_local": "ISO local datetime",
                    "end_local": "ISO local datetime or empty",
                    "is_important": "bool",
                    "is_recurring": "bool",
                    "recurrence": {
                        "freq": "none|daily|weekly|monthly|weekdays|every_n_weeks",
                        "interval": "integer",
                        "byweekday": [0, 1, 2, 3, 4, 5, 6],
                        "end_type": "never|count|until",
                        "count": "integer or null",
                        "until_local": "ISO local datetime or empty",
                    },
                    "confidence_10": "1..10",
                }
            ],
            "notes": "string",
        }
        user_payload = {
            "now_local_iso": now_local_iso,
            "timezone": tz_name,
            "caption": caption,
            "schema": schema,
        }
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": json.dumps(user_payload)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"events": [], "notes": ""}
        return parsed if isinstance(parsed, dict) else {"events": [], "notes": ""}


def normalize_recurrence(raw: dict[str, Any] | None, start_utc: datetime) -> dict[str, Any]:
    incoming = raw if isinstance(raw, dict) else {}
    freq = str(incoming.get("freq", "daily")).strip().lower()
    if freq in {"", "none"}:
        freq = "daily"
    if freq not in {"daily", "weekly", "monthly", "weekdays", "every_n_weeks"}:
        freq = "daily"
    try:
        interval = int(incoming.get("interval", 1))
    except Exception:
        interval = 1
    interval = max(1, min(interval, 30))

    weekdays = incoming.get("byweekday", [start_utc.weekday()])
    byweekday: list[int] = []
    if isinstance(weekdays, list):
        for item in weekdays:
            try:
                day = int(item)
            except Exception:
                continue
            if 0 <= day <= 6:
                byweekday.append(day)
    if not byweekday:
        byweekday = [start_utc.weekday()]

    end_type = str(incoming.get("end_type", "never")).strip().lower()
    if end_type not in {"never", "count", "until"}:
        end_type = "never"

    count_value: int | None = None
    if end_type == "count":
        try:
            count_value = max(1, min(int(incoming.get("count", 1)), 5000))
        except Exception:
            count_value = 1

    until_utc = incoming.get("until_utc")
    if isinstance(until_utc, str) and until_utc.strip():
        try:
            until_utc = parse_iso_utc(until_utc).isoformat()
        except Exception:
            until_utc = None
    else:
        until_utc = None
    if end_type == "until" and not until_utc:
        end_type = "never"

    return {
        "freq": freq,
        "interval": interval,
        "byweekday": byweekday,
        "end_type": end_type,
        "count": count_value if end_type == "count" else None,
        "until_utc": until_utc if end_type == "until" else None,
    }


def build_rrule(event: Event) -> rrule:
    rule = event.recurrence_rule or {}
    freq = str(rule.get("freq", "daily")).lower()
    interval = int(rule.get("interval", 1) or 1)
    kwargs: dict[str, Any] = {"interval": max(1, interval)}

    if freq == "daily":
        rr_freq = DAILY
    elif freq == "weekly":
        rr_freq = WEEKLY
        byweekday = [WEEKDAY_MAP[d] for d in rule.get("byweekday", []) if d in WEEKDAY_MAP]
        if byweekday:
            kwargs["byweekday"] = byweekday
    elif freq == "monthly":
        rr_freq = MONTHLY
    elif freq == "weekdays":
        rr_freq = WEEKLY
        kwargs["interval"] = 1
        kwargs["byweekday"] = [MO, TU, WE, TH, FR]
    elif freq == "every_n_weeks":
        rr_freq = WEEKLY
        days = rule.get("byweekday", [event.start_dt_utc.weekday()])
        byweekday = [WEEKDAY_MAP[d] for d in days if d in WEEKDAY_MAP]
        kwargs["byweekday"] = byweekday or [WEEKDAY_MAP[event.start_dt_utc.weekday()]]
    else:
        rr_freq = DAILY

    end_type = str(rule.get("end_type", "never")).lower()
    if end_type == "count" and rule.get("count"):
        kwargs["count"] = max(1, int(rule["count"]))
    elif end_type == "until" and rule.get("until_utc"):
        kwargs["until"] = parse_iso_utc(str(rule["until_utc"]))
    return rrule(rr_freq, dtstart=event.start_dt_utc, **kwargs)


def expand_occurrences(event: Event, *, start_utc: datetime, end_utc: datetime, overrides: list[sqlite3.Row], max_items: int = 500) -> list[Occurrence]:
    if event.status != "active" or end_utc <= start_utc:
        return []

    duration = event.end_dt_utc - event.start_dt_utc
    if duration.total_seconds() <= 0:
        duration = timedelta(hours=1)

    override_map = {str(row["occurrence_start_utc"]): row for row in overrides}
    items: list[Occurrence] = []

    if not event.is_recurring:
        st = event.start_dt_utc
        ed = event.end_dt_utc
        row = override_map.get(event.start_at_utc)
        if row and row["status"] in {"done", "deleted"}:
            return []
        if row and row["status"] == "rescheduled" and row["rescheduled_start_utc"]:
            st = parse_iso_utc(row["rescheduled_start_utc"])
            ed = parse_iso_utc(row["rescheduled_end_utc"]) if row["rescheduled_end_utc"] else st + duration
        if st <= end_utc and ed >= start_utc:
            items.append(Occurrence(event.id, event.title, st, ed, event.is_important, event.start_dt_utc))
        return items

    starts = list(build_rrule(event).between(start_utc - duration, end_utc, inc=True))
    for st in starts[:max_items]:
        key = st.isoformat()
        ov = override_map.get(key)
        if ov and ov["status"] in {"done", "deleted"}:
            continue
        if ov and ov["status"] == "rescheduled" and ov["rescheduled_start_utc"]:
            st2 = parse_iso_utc(ov["rescheduled_start_utc"])
            ed2 = parse_iso_utc(ov["rescheduled_end_utc"]) if ov["rescheduled_end_utc"] else st2 + duration
            if st2 <= end_utc and ed2 >= start_utc:
                items.append(Occurrence(event.id, event.title, st2, ed2, event.is_important, st))
            continue
        ed = st + duration
        if st <= end_utc and ed >= start_utc:
            items.append(Occurrence(event.id, event.title, st, ed, event.is_important, st))

    items.sort(key=lambda x: x.start_at_utc)
    return items[:max_items]


def recurrence_text(rule: dict[str, Any]) -> str:
    freq = str(rule.get("freq", "daily")).lower()
    interval = int(rule.get("interval", 1) or 1)
    if freq == "daily":
        label = "daily" if interval == 1 else f"every {interval} days"
    elif freq == "weekly":
        label = "weekly" if interval == 1 else f"every {interval} weeks"
    elif freq == "monthly":
        label = "monthly" if interval == 1 else f"every {interval} months"
    elif freq == "weekdays":
        label = "weekdays"
    elif freq == "every_n_weeks":
        label = f"every {interval} weeks"
    else:
        label = "daily"
    end_type = str(rule.get("end_type", "never")).lower()
    if end_type == "count" and rule.get("count"):
        return f"{label}, {int(rule['count'])} occurrences"
    if end_type == "until" and rule.get("until_utc"):
        return f"{label}, until {str(rule['until_utc'])[:10]}"
    return label

class Agent:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.tz = ZoneInfo(config.timezone_name)
        self.store = StateStore()
        self.telegram = TelegramClient(config.telegram_bot_token, config.telegram_chat_id)
        self.analyzer = Analyzer(config)
        self.scheduler = BackgroundScheduler(timezone=self.tz)

    def _next_occurrence(self, event: Event) -> Occurrence | None:
        now = utc_now()
        occs = expand_occurrences(
            event,
            start_utc=now - timedelta(minutes=1),
            end_utc=now + timedelta(days=365),
            overrides=self.store.get_overrides_for_event(event.id),
            max_items=300,
        )
        for occ in occs:
            if occ.end_at_utc >= now:
                return occ
        return None

    def _upcoming_samples(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for event in self.store.list_active_events():
            nxt = self._next_occurrence(event)
            if not nxt:
                continue
            rows.append(
                {
                    "event_id": event.id,
                    "title": event.title,
                    "category": event.category,
                    "course_number": event.course_number,
                    "location": event.location or "none",
                    "next_start_local": nxt.start_at_utc.astimezone(self.tz).isoformat(),
                    "is_recurring": event.is_recurring,
                    "is_important": event.is_important,
                }
            )
        rows.sort(key=lambda x: x["next_start_local"])
        return rows[:8]

    def _build_recurrence(self, raw: dict[str, Any] | None, start_utc: datetime) -> dict[str, Any]:
        base = raw if isinstance(raw, dict) else {}
        freq_token = str(base.get("freq", "")).strip().lower()
        if freq_token in {"", "none"}:
            return {}
        until_local = str(base.get("until_local", "")).strip()
        until_utc: str | None = None
        if until_local:
            dt = parse_local_flexible_to_utc(until_local, self.tz)
            if dt:
                until_utc = dt.isoformat()
        temp = {
            "freq": base.get("freq"),
            "interval": base.get("interval", 1),
            "byweekday": base.get("byweekday", [start_utc.weekday()]),
            "end_type": base.get("end_type", "never"),
            "count": base.get("count"),
            "until_utc": until_utc,
        }
        return normalize_recurrence(temp, start_utc)

    def _normalize_create_payload(self, create_data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(create_data)
        normalized["is_important"] = to_bool(create_data.get("is_important"), default=False)
        explicit_recurring = to_bool(create_data.get("is_recurring"), default=False)
        recurrence_raw = create_data.get("recurrence")
        recurrence_freq = ""
        if isinstance(recurrence_raw, dict):
            recurrence_freq = str(recurrence_raw.get("freq", "")).strip().lower()
        normalized["is_recurring"] = explicit_recurring or recurrence_freq not in {"", "none"}
        location = str(create_data.get("location", "")).strip()
        normalized["location"] = location if location else "none"
        normalized["category"] = normalize_category(
            create_data.get("category"),
            create_data.get("title", ""),
            create_data.get("description", ""),
        )
        normalized["course_number"] = normalize_course_number(
            create_data.get("course_number"),
            create_data.get("title", ""),
            create_data.get("description", ""),
        )
        return normalized

    def _save_pending(self, key: str, payload: dict[str, Any]) -> None:
        self.store.set(key, json.dumps(payload))

    def _load_pending(self, key: str) -> dict[str, Any] | None:
        raw = self.store.get(key, "")
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except Exception:
            return None
        return data if isinstance(data, dict) else None

    def _clear_pending(self, key: str) -> None:
        self.store.delete(key)

    def _format_create_preview(self, create_data: dict[str, Any], idx: int) -> str:
        title = str(create_data.get("title", "")).strip() or f"Untitled {idx}"
        start_local = str(create_data.get("start_local", "")).strip()
        end_local = str(create_data.get("end_local", "")).strip()
        location = str(create_data.get("location", "none")).strip() or "none"
        category_value = normalize_category(create_data.get("category"), title, create_data.get("description", ""))
        category = category_label(category_value)
        course_line = format_course_line(
            category_value,
            normalize_course_number(create_data.get("course_number"), title, create_data.get("description", "")),
        )
        importance = "IMPORTANT" if to_bool(create_data.get("is_important"), default=False) else "NORMAL"
        recurring = to_bool(create_data.get("is_recurring"), default=False)
        recurrence_label = "none"
        if recurring:
            built = self._build_recurrence(create_data.get("recurrence"), parse_local_flexible_to_utc(start_local, self.tz) or utc_now())
            recurrence_label = recurrence_text(built) if built else "none"
        lines = [
            f"{idx}. {title}",
            f"   Category: {category}",
        ]
        if course_line:
            lines.append(f"   {course_line}")
        lines.extend(
            [
                f"   When: {start_local or '?'} -> {end_local or '(default +1h)'}",
                f"   Where: {location}",
                f"   Type: {importance}",
                f"   Repeat: {recurrence_label}",
            ]
        )
        return "\n".join(lines)

    def _handle_pending_image_confirmation(self, text: str) -> bool:
        pending = self._load_pending("pending_image_confirmation")
        if not pending:
            return False
        command = text.strip().lower()
        if command in {"confirm", "/confirm", "yes", "y", "ok"}:
            events = pending.get("events", [])
            if not isinstance(events, list) or not events:
                self._clear_pending("pending_image_confirmation")
                self.telegram.send_message("No extracted schedule to confirm.")
                return True
            created_ids: list[int] = []
            failed_count = 0
            for raw in events[:12]:
                if not isinstance(raw, dict):
                    failed_count += 1
                    continue
                event = self._handle_create(raw, "photo_import", notify=False)
                if event is not None:
                    created_ids.append(event.id)
                else:
                    failed_count += 1
            self._clear_pending("pending_image_confirmation")
            if created_ids:
                summary = f"Imported {len(created_ids)} schedule item(s) from image."
                if failed_count:
                    summary += f" ({failed_count} item(s) skipped due to invalid datetime.)"
                now = utc_now()
                created_events = [self.store.get_event(eid) for eid in created_ids]
                past_count = sum(1 for e in created_events if e.end_dt_utc < now)
                if past_count:
                    summary += f" {past_count} imported item(s) are already expired and may not appear as future events."
                self.telegram.send_message(summary)
                self._send_upcoming()
            else:
                self.telegram.send_message("No valid schedule items were imported.")
            return True
        if command in {"cancel", "/cancel", "no", "n"}:
            self._clear_pending("pending_image_confirmation")
            self.telegram.send_message("Image schedule import canceled.")
            return True
        self.telegram.send_message(
            "You have pending schedule extraction from image. Reply `confirm` to save or `cancel` to discard."
        )
        return True

    def _looks_like_clear_all_request(self, text: str) -> bool:
        lowered = text.strip().lower()
        if not lowered:
            return False
        direct_phrases = [
            "clear all schedule",
            "clear all schedules",
            "clear my schedule",
            "reset all schedule",
            "reset all schedules",
            "reset my schedule",
            "delete all schedule",
            "delete all schedules",
            "remove all schedule",
            "remove all schedules",
            "wipe all schedule",
            "wipe all schedules",
            "clear everything in schedule",
            "reset everything in schedule",
            "clear all calendar",
            "reset all calendar",
            "清空所有日程",
            "清空全部日程",
            "删除所有日程",
            "删除全部日程",
            "重置所有日程",
            "重置全部日程",
            "清空所有安排",
            "清空全部安排",
            "清空所有行程",
            "清空全部行程",
        ]
        if any(phrase in lowered for phrase in direct_phrases):
            return True
        action_words = ["clear", "reset", "delete", "remove", "wipe", "清空", "删除", "重置"]
        scope_words = ["all", "everything", "全部", "所有"]
        object_words = ["schedule", "schedules", "calendar", "events", "日程", "安排", "行程"]
        return (
            any(word in lowered for word in action_words)
            and any(word in lowered for word in scope_words)
            and any(word in lowered for word in object_words)
        )

    def _request_clear_all(self) -> None:
        counts = self.store.schedule_data_counts()
        if not any(counts.values()):
            self.telegram.send_message("No saved schedule data found. Nothing to clear.")
            return
        self._clear_pending("pending_image_confirmation")
        self._clear_pending("pending_selection")
        self._clear_pending("pending_reschedule")
        self._save_pending(
            "pending_clear_all",
            {
                "counts": counts,
                "requested_at_utc": utc_now().isoformat(),
            },
        )
        self.telegram.send_message(
            "Clear All Confirmation\n"
            f"Active schedules: {counts['active_events']}\n"
            f"Stored events/history: {counts['total_events']}\n"
            f"Recurring overrides: {counts['occurrence_overrides']}\n"
            f"Reminder logs: {counts['reminder_logs']}\n"
            f"Snoozed reminders: {counts['snoozed_reminders']}\n\n"
            "Reply `confirm clear all` or `/confirm_clear_all` to delete all saved schedule data.\n"
            "Reply `cancel` to keep everything."
        )

    def _handle_pending_clear_all(self, text: str) -> bool:
        pending = self._load_pending("pending_clear_all")
        if not pending:
            return False
        command = text.strip().lower()
        if command in {"confirm clear all", "/confirm_clear_all"}:
            counts = self.store.clear_all_schedule_data()
            self._clear_pending("pending_clear_all")
            self.telegram.send_message(
                "Cleared all schedule data.\n"
                f"Removed events/history: {counts['total_events']}\n"
                f"Removed recurring overrides: {counts['occurrence_overrides']}\n"
                f"Removed reminder logs: {counts['reminder_logs']}\n"
                f"Removed snoozed reminders: {counts['snoozed_reminders']}"
            )
            return True
        if command in {"cancel", "/cancel"}:
            self._clear_pending("pending_clear_all")
            self.telegram.send_message("Clear-all request canceled.")
            return True
        if command in {"confirm", "/confirm", "yes", "y"}:
            self.telegram.send_message(
                "For safety, reply `confirm clear all` or `/confirm_clear_all` to delete everything. Reply `cancel` to keep everything."
            )
            return True
        self.telegram.send_message(
            "Pending clear-all request. Reply `confirm clear all` or `/confirm_clear_all` to proceed, or `cancel` to stop."
        )
        return True

    def _format_event(self, event: Event, occ: Occurrence) -> str:
        kind = "IMPORTANT" if event.is_important else "NORMAL"
        category_value = normalize_category(event.category, event.title, event.description, event.source_text)
        category = category_label(category_value)
        course_line = format_course_line(category_value, event.course_number)
        start = occ.start_at_utc.astimezone(self.tz).strftime("%Y-%m-%d %I:%M %p")
        end = occ.end_at_utc.astimezone(self.tz).strftime("%Y-%m-%d %I:%M %p")
        repeat = recurrence_text(event.recurrence_rule) if event.is_recurring else "none"
        lines = [
            f"#E{event.id} | {event.title}",
            f"Category: {category} | Type: {kind}",
        ]
        if course_line:
            lines.append(course_line)
        lines.extend(
            [
                f"Repeat: {repeat}",
                f"When: {start} -> {end}",
                f"Where: {event.location or 'none'}",
            ]
        )
        return "\n".join(lines)

    def _send_upcoming(self) -> None:
        now = utc_now()
        rows_by_category: dict[str, list[tuple[datetime, bool, str]]] = {"submission": [], "upcoming": []}
        for event in self.store.list_active_events():
            category = normalize_category(event.category, event.title, event.description, event.source_text)
            overrides = self.store.get_overrides_for_event(event.id)
            next_items = expand_occurrences(
                event,
                start_utc=now - timedelta(minutes=1),
                end_utc=now + timedelta(days=365),
                overrides=overrides,
                max_items=300,
            )
            next_occ = next((o for o in next_items if o.end_at_utc >= now), None)
            if next_occ:
                rows_by_category[category].append((next_occ.start_at_utc, False, self._format_event(event, next_occ)))
                continue

            recent_items = expand_occurrences(
                event,
                start_utc=now - timedelta(days=3),
                end_utc=now,
                overrides=overrides,
                max_items=120,
            )
            recent_past = [o for o in recent_items if o.end_at_utc < now]
            if recent_past:
                occ = sorted(recent_past, key=lambda x: x.start_at_utc, reverse=True)[0]
                rows_by_category[category].append(
                    (
                        occ.start_at_utc,
                        True,
                        "\U0001F534 EXPIRED\n" + self._format_event(event, occ),
                    )
                )

        if not any(rows_by_category.values()):
            self.telegram.send_message("No upcoming schedule.")
            return

        lines = [f"Schedule Overview ({datetime.now(self.tz).strftime('%Y-%m-%d %I:%M %p')})", ""]
        for category in ("submission", "upcoming"):
            section_title = "Submission" if category == "submission" else "Upcoming Schedule"
            section_rows = rows_by_category[category]
            section_rows.sort(key=lambda item: (item[1], item[0]))
            lines.append(section_title)
            lines.append("")
            if not section_rows:
                lines.append("No items.")
                lines.append("")
                continue
            for idx, (_, is_expired, line) in enumerate(section_rows, start=1):
                lines.append(f"{idx}) {line}")
                if is_expired:
                    lines.append("   Note: Removed automatically after 3 days from end time.")
                lines.append("")
                if len("\n".join(lines)) > 3600:
                    lines.append("...truncated.")
                    self.telegram.send_message("\n".join(lines))
                    return
        self.telegram.send_message("\n".join(lines))

    def _send_history(self, days: int) -> None:
        days = max(1, min(days, 180))
        now = utc_now()
        start = now - timedelta(days=days)
        lines = [f"History (last {days} days)", ""]
        rows_by_category: dict[str, list[tuple[datetime, str]]] = {"submission": [], "upcoming": []}

        def append_history_row(event: Event, start_dt: datetime, end_dt: datetime) -> None:
            category = normalize_category(event.category, event.title, event.description, event.source_text)
            occ = Occurrence(
                event_id=event.id,
                title=event.title,
                start_at_utc=start_dt,
                end_at_utc=end_dt,
                is_important=event.is_important,
                source_occurrence_start_utc=start_dt,
            )
            rows_by_category[category].append((start_dt, "\U0001F534 EXPIRED\n" + self._format_event(event, occ)))

        active = self.store.list_active_events()
        for event in [e for e in active if not e.is_recurring]:
            if start <= event.end_dt_utc < now:
                append_history_row(event, event.start_dt_utc, event.end_dt_utc)

        count = 0
        for event in [e for e in active if e.is_recurring]:
            occs = expand_occurrences(
                event,
                start_utc=start,
                end_utc=now,
                overrides=self.store.get_overrides_for_event(event.id),
                max_items=250,
            )
            for occ in sorted(occs, key=lambda o: o.start_at_utc, reverse=True):
                if occ.end_at_utc >= now:
                    continue
                append_history_row(event, occ.start_at_utc, occ.end_at_utc)
                count += 1
                if count >= 60:
                    break
            if count >= 60:
                break

        if not any(rows_by_category.values()):
            lines.append("No expired events in this range.")
            self.telegram.send_message("\n".join(lines)[:3900])
            return

        for category in ("submission", "upcoming"):
            section_rows = rows_by_category[category]
            if not section_rows:
                continue
            section_title = "Submission" if category == "submission" else "Upcoming Schedule"
            section_rows.sort(key=lambda item: item[0], reverse=True)
            lines.append(section_title)
            lines.append("")
            for idx, (_, line) in enumerate(section_rows, start=1):
                lines.append(f"{idx}) {line}")
                lines.append("")
                if len("\n".join(lines)) > 3600:
                    lines.append("...history truncated.")
                    self.telegram.send_message("\n".join(lines)[:3900])
                    return
        self.telegram.send_message("\n".join(lines)[:3900])
    def _selection_prompt(self, event_ids: list[int], action: str) -> str:
        lines = [f"I found {len(event_ids)} matches for {action}. Reply with number or #E<id>.", ""]
        for idx, eid in enumerate(event_ids, start=1):
            event = self.store.get_event(eid)
            nxt = self._next_occurrence(event)
            when = (nxt.start_at_utc if nxt else event.start_dt_utc).astimezone(self.tz).strftime("%Y-%m-%d %I:%M %p")
            lines.append(f"{idx}) #E{event.id} {event.title}")
            lines.append(
                f"   Category: {category_label(normalize_category(event.category, event.title, event.description, event.source_text))} | Next: {when}"
            )
            course_line = format_course_line(event.category, event.course_number)
            if course_line:
                lines.append(f"   {course_line}")
            lines.append(f"   Where: {event.location or 'none'}")
        lines.append("Reply 'cancel' to stop.")
        return "\n".join(lines)

    def _apply_mutation(self, event: Event, intent: str, changes: dict[str, Any]) -> str:
        if intent == "delete":
            self.store.delete_event(event.id)
            return f"Deleted #E{event.id} | {event.title}"
        if intent == "mark_important":
            updated = self.store.update_event_fields(event.id, {"is_important": True})
            lines = [
                f"Updated #E{updated.id} | {updated.title}",
                f"Category: {category_label(updated.category)}",
            ]
            course_line = format_course_line(updated.category, updated.course_number)
            if course_line:
                lines.append(course_line)
            lines.append("Type: IMPORTANT")
            return "\n".join(lines)
        if intent == "mark_normal":
            updated = self.store.update_event_fields(event.id, {"is_important": False})
            lines = [
                f"Updated #E{updated.id} | {updated.title}",
                f"Category: {category_label(updated.category)}",
            ]
            course_line = format_course_line(updated.category, updated.course_number)
            if course_line:
                lines.append(course_line)
            lines.append("Type: NORMAL")
            return "\n".join(lines)

        current = self.store.get_event(event.id)
        duration = current.end_dt_utc - current.start_dt_utc
        if duration.total_seconds() <= 0:
            duration = timedelta(hours=1)

        updates: dict[str, Any] = {}
        title = str(changes.get("title", "")).strip()
        desc = str(changes.get("description", "")).strip()
        location = str(changes.get("location", "")).strip()
        category = str(changes.get("category", "")).strip()
        course_number = str(changes.get("course_number", "")).strip()
        if title:
            updates["title"] = title[:200]
        if desc:
            updates["description"] = desc[:800]
        if location:
            updates["location"] = location[:180]
        if category:
            updates["category"] = normalize_category(category, current.title, current.description, current.source_text)
        if course_number:
            updates["course_number"] = normalize_course_number(
                course_number,
                title or current.title,
                desc or current.description,
                current.source_text,
            )

        new_start = parse_local_flexible_to_utc(str(changes.get("start_local", "")).strip(), self.tz)
        new_end = parse_local_flexible_to_utc(str(changes.get("end_local", "")).strip(), self.tz)
        if changes.get("duration_minutes") is not None:
            try:
                duration = timedelta(minutes=max(1, int(changes["duration_minutes"])))
            except Exception:
                pass
        if new_start and not new_end:
            new_end = new_start + duration
        if new_end and not new_start:
            new_start = current.start_dt_utc
        if new_start and new_end and new_end <= new_start:
            new_end = new_start + timedelta(hours=1)
        if new_start:
            updates["start_at_utc"] = new_start.isoformat()
        if new_end:
            updates["end_at_utc"] = new_end.isoformat()

        set_recurring = to_optional_bool(changes.get("set_recurring"))
        rec = changes.get("recurrence")
        if set_recurring is False:
            updates["is_recurring"] = False
            updates["recurrence_rule"] = {}
        elif set_recurring is True or (isinstance(rec, dict) and rec):
            base_start = parse_iso_utc(updates.get("start_at_utc", current.start_at_utc))
            built = self._build_recurrence(rec if isinstance(rec, dict) else None, base_start)
            if built:
                updates["is_recurring"] = True
                updates["recurrence_rule"] = built
            else:
                updates["is_recurring"] = False
                updates["recurrence_rule"] = {}

        if not updates:
            return "No update fields recognized."
        updated = self.store.update_event_fields(event.id, updates)
        repeat = recurrence_text(updated.recurrence_rule) if updated.is_recurring else "none"
        lines = [
            f"Updated #E{updated.id} | {updated.title}",
            f"Category: {category_label(updated.category)}",
        ]
        course_line = format_course_line(updated.category, updated.course_number)
        if course_line:
            lines.append(course_line)
        lines.extend(
            [
                f"When: {fmt_local(updated.start_at_utc, self.tz)} -> {fmt_local(updated.end_at_utc, self.tz)}",
                f"Where: {updated.location or 'none'}",
                f"Type: {'IMPORTANT' if updated.is_important else 'NORMAL'} | Repeat: {repeat}",
            ]
        )
        return "\n".join(lines)

    def _resolve_and_apply(self, intent: str, target_query: str, changes: dict[str, Any]) -> None:
        matches = self.store.search_active_events(target_query)
        if not matches:
            self.telegram.send_message("No matching event found. Try #E12 or a clearer title.")
            return
        if len(matches) > 1:
            payload = {"intent": intent, "event_ids": [e.id for e in matches], "changes": changes}
            self._save_pending("pending_selection", payload)
            self.telegram.send_message(self._selection_prompt(payload["event_ids"], intent))
            return
        selected = matches[0]
        self.telegram.send_message(self._apply_mutation(selected, intent, changes))
        self.store.set("last_event_id", str(selected.id))

    def _active_events_by_ids(self, event_ids: list[int]) -> tuple[list[Event], list[int]]:
        events: list[Event] = []
        missing: list[int] = []
        seen: set[int] = set()
        for raw_id in event_ids:
            try:
                event_id = int(raw_id)
            except Exception:
                continue
            if event_id in seen:
                continue
            seen.add(event_id)
            try:
                event = self.store.get_event(event_id)
            except Exception:
                missing.append(event_id)
                continue
            if event.status != "active":
                missing.append(event_id)
                continue
            events.append(event)
        return events, missing

    def _extract_bulk_target_ids(self, text: str) -> list[int] | None:
        raw = text.strip()
        lowered = raw.lower()
        if not raw:
            return None

        active_events = self.store.list_active_events()
        if not active_events:
            return None

        def unique_order(ids: list[int]) -> list[int]:
            seen: set[int] = set()
            ordered: list[int] = []
            for event_id in ids:
                if event_id in seen:
                    continue
                seen.add(event_id)
                ordered.append(event_id)
            return ordered

        if any(token in lowered for token in ["all submissions", "all submission", "all deadlines", "所有提交", "全部提交"]):
            ids = [event.id for event in active_events if normalize_category(event.category) == "submission"]
            return ids or None

        if any(token in lowered for token in ["all upcoming", "all upcoming schedules", "all upcoming schedule", "所有日程", "全部日程"]):
            ids = [event.id for event in active_events if normalize_category(event.category) == "upcoming"]
            return ids or None

        if any(token in lowered for token in ["all schedules", "all schedule", "all events", "all tasks"]):
            ids = [event.id for event in active_events]
            return ids or None

        range_match = re.search(r"\b(?:all\s+)?(?:from\s+)?E(\d+)\s*(?:to|through|thru|-)\s*E?(\d+)\b", raw, re.IGNORECASE)
        if range_match:
            start_id = int(range_match.group(1))
            end_id = int(range_match.group(2))
            low, high = sorted((start_id, end_id))
            ids = [event.id for event in active_events if low <= event.id <= high]
            return ids if len(ids) > 1 else None

        explicit_ids = unique_order([int(match) for match in re.findall(r"\bE(\d+)\b", raw, re.IGNORECASE)])
        if len(explicit_ids) > 1:
            events, _ = self._active_events_by_ids(explicit_ids)
            ids = [event.id for event in events]
            return ids if len(ids) > 1 else None
        return None

    def _apply_bulk_mutation(self, events: list[Event], intent: str, changes: dict[str, Any], missing_ids: list[int] | None = None) -> str:
        if not events:
            return "No matching event found."

        if len(events) == 1:
            return self._apply_mutation(events[0], intent, changes)

        updated_events: list[Event] = []
        deleted_events: list[Event] = []
        ignored_count = 0
        for event in events:
            result = self._apply_mutation(event, intent, changes)
            if result == "No update fields recognized.":
                ignored_count += 1
                continue
            if intent == "delete":
                deleted_events.append(event)
            else:
                try:
                    updated_events.append(self.store.get_event(event.id))
                except Exception:
                    deleted_events.append(event)
            self.store.set("last_event_id", str(event.id))

        changed_count = len(updated_events) + len(deleted_events)
        if changed_count == 0:
            return "No update fields recognized."

        if intent == "delete":
            lines = [f"Deleted {changed_count} schedules."]
            for idx, event in enumerate(deleted_events[:8], start=1):
                lines.append(f"{idx}) #E{event.id} {event.title}")
        else:
            action_map = {
                "update": "Updated",
                "mark_important": "Marked important",
                "mark_normal": "Marked normal",
            }
            lines = [f"{action_map.get(intent, 'Updated')} {changed_count} schedules."]
            for idx, event in enumerate(updated_events[:8], start=1):
                next_occ = self._next_occurrence(event)
                next_time = (next_occ.start_at_utc if next_occ else event.start_dt_utc).astimezone(self.tz).strftime("%Y-%m-%d %I:%M %p")
                lines.append(f"{idx}) #E{event.id} {event.title}")
                lines.append(f"   Category: {category_label(event.category)} | Next: {next_time}")
                course_line = format_course_line(event.category, event.course_number)
                if course_line:
                    lines.append(f"   {course_line}")
                lines.append(f"   Where: {event.location or 'none'}")

        extra = changed_count - 8
        if extra > 0:
            lines.append(f"...and {extra} more.")
        if missing_ids:
            lines.append(f"Ignored missing/inactive IDs: {', '.join(f'E{event_id}' for event_id in missing_ids[:8])}")
        if ignored_count:
            lines.append(f"Ignored {ignored_count} item(s) because no update field was recognized.")
        return "\n".join(lines)

    def _resolve_bulk_and_apply(self, intent: str, event_ids: list[int], changes: dict[str, Any]) -> None:
        events, missing_ids = self._active_events_by_ids(event_ids)
        if not events:
            self.telegram.send_message("No matching event found. Try a valid ID range like E1 to E6.")
            return
        self.telegram.send_message(self._apply_bulk_mutation(events, intent, changes, missing_ids))

    def _request_selection_without_query(self, intent: str, changes: dict[str, Any]) -> None:
        active = self.store.list_active_events()
        if not active:
            self.telegram.send_message("No active schedule found.")
            return
        if len(active) == 1:
            selected = active[0]
            self.telegram.send_message(self._apply_mutation(selected, intent, changes))
            self.store.set("last_event_id", str(selected.id))
            return
        ids = [e.id for e in active[:20]]
        payload = {"intent": intent, "event_ids": ids, "changes": changes}
        self._save_pending("pending_selection", payload)
        self.telegram.send_message(self._selection_prompt(ids, intent))

    def _extract_recurrence_change(self, text: str) -> dict[str, Any] | None:
        lowered = text.strip().lower()
        if not lowered:
            return None
        has_action = any(k in lowered for k in ["change", "set", "update", "make", "turn", "switch", "edit"])
        has_repeat = any(k in lowered for k in ["recurr", "repeat", "recurrence"])
        if not (has_action and has_repeat):
            return None

        if any(k in lowered for k in ["none", "no repeat", "not recurring", "one-time", "one time"]):
            return {"set_recurring": False, "recurrence": {"freq": "none"}}

        every_n_weeks = re.search(r"every\s+(\d+)\s+weeks?", lowered)
        if every_n_weeks:
            return {
                "set_recurring": True,
                "recurrence": {
                    "freq": "every_n_weeks",
                    "interval": max(1, int(every_n_weeks.group(1))),
                    "byweekday": [],
                    "end_type": "never",
                    "count": None,
                    "until_local": "",
                },
            }

        freq = ""
        if any(k in lowered for k in ["daily", "every day"]):
            freq = "daily"
        elif any(k in lowered for k in ["weekly", "every week"]):
            freq = "weekly"
        elif any(k in lowered for k in ["monthly", "every month"]):
            freq = "monthly"
        elif any(k in lowered for k in ["weekday", "weekdays", "workday"]):
            freq = "weekdays"
        if not freq:
            return None
        return {
            "set_recurring": True,
            "recurrence": {
                "freq": freq,
                "interval": 1,
                "byweekday": [],
                "end_type": "never",
                "count": None,
                "until_local": "",
            },
        }

    def _extract_category_change(self, text: str) -> dict[str, Any] | None:
        lowered = text.strip().lower()
        if not lowered:
            return None
        has_action = any(k in lowered for k in ["change", "set", "update", "move", "switch", "mark", "edit", "分类", "改成", "设为", "设置"])
        if not has_action:
            return None
        if any(k in lowered for k in ["submission", "deadline", "due", "submit", "ddl", "截止", "提交", "作业"]):
            return {"category": "submission"}
        if any(k in lowered for k in ["upcoming", "schedule", "event", "日程", "安排", "行程"]):
            return {"category": "upcoming"}
        return None

    def _extract_course_number_change(self, text: str) -> dict[str, Any] | None:
        lowered = text.strip().lower()
        if not lowered:
            return None
        action_words = ["change", "set", "update", "edit", "replace", "mark", "use", "改", "设", "设置", "更新"]
        course_words = [
            "course number",
            "course no",
            "course code",
            "module code",
            "module number",
            "module no",
            "课程号",
            "课程编号",
            "课程代码",
            "科目代码",
        ]
        if not (any(word in lowered for word in action_words) and any(word in lowered for word in course_words)):
            return None

        clear_terms = ["none", "remove", "clear", "delete", "empty", "无", "清空", "删除"]
        if any(term in lowered for term in clear_terms):
            return {"course_number": "none"}

        patterns = [
            r"(?i)(?:course\s*(?:number|no\.?|code)?|module\s*(?:code|number|no\.?)?)\s*(?:to|as|=|is)?\s*[:：]?\s*([A-Za-z]{2,8}\s*[-/]?\s*\d{2,6}[A-Za-z]?)",
            r"(?:课程(?:号|编号|代码)?|科目代码)\s*(?:改成|设为|设置为|是|为|to)?\s*[:：]?\s*([A-Za-z]{2,8}\s*[-/]?\s*\d{2,6}[A-Za-z]?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return {"course_number": normalize_course_number(match.group(1))}
        return None

    def _handle_pending_selection(self, text: str) -> bool:
        pending = self._load_pending("pending_selection")
        if not pending:
            return False
        value = text.strip()
        if value.lower() == "cancel":
            self._clear_pending("pending_selection")
            self.telegram.send_message("Canceled.")
            return True
        ids = [int(i) for i in pending.get("event_ids", [])]
        selected_id: int | None = None

        if re.fullmatch(r"\d+", value):
            idx = int(value)
            if 1 <= idx <= len(ids):
                selected_id = ids[idx - 1]
        if selected_id is None:
            match = re.search(r"\bE(\d+)\b", value.upper())
            if match:
                eid = int(match.group(1))
                if eid in ids:
                    selected_id = eid
        if selected_id is None:
            filtered = []
            needle = value.lower()
            for eid in ids:
                event = self.store.get_event(eid)
                if needle in f"{event.title} {event.description} {event.course_number} {event.location} {event.source_text}".lower():
                    filtered.append(eid)
            if len(filtered) == 1:
                selected_id = filtered[0]
            elif len(filtered) > 1:
                pending["event_ids"] = filtered
                self._save_pending("pending_selection", pending)
                self.telegram.send_message(self._selection_prompt(filtered, pending.get("intent", "update")))
                return True
            else:
                self.telegram.send_message(self._selection_prompt(ids, pending.get("intent", "update")))
                return True

        if selected_id is None:
            self.telegram.send_message(self._selection_prompt(ids, pending.get("intent", "update")))
            return True

        event = self.store.get_event(selected_id)
        intent = str(pending.get("intent", "update"))
        changes = pending.get("changes", {})
        self.telegram.send_message(self._apply_mutation(event, intent, changes if isinstance(changes, dict) else {}))
        self.store.set("last_event_id", str(event.id))
        self._clear_pending("pending_selection")
        return True

    def _handle_pending_reschedule(self, text: str) -> bool:
        pending = self._load_pending("pending_reschedule")
        if not pending:
            return False
        if text.strip().lower() == "cancel":
            self._clear_pending("pending_reschedule")
            self.telegram.send_message("Reschedule canceled.")
            return True
        token = str(pending.get("token", ""))
        row = self.store.get_action_token(token)
        if not row:
            self._clear_pending("pending_reschedule")
            self.telegram.send_message("Reschedule target expired. Trigger reminder again.")
            return True

        parsed = self.analyzer.parse_datetime_message(
            text=text,
            now_local_iso=datetime.now(self.tz).isoformat(),
            tz_name=self.config.timezone_name,
        )
        new_start = parse_local_flexible_to_utc(parsed.get("start_local", ""), self.tz)
        new_end = parse_local_flexible_to_utc(parsed.get("end_local", ""), self.tz)
        if not new_start:
            self.telegram.send_message("Cannot parse datetime. Example: tomorrow 4pm")
            return True

        event = self.store.get_event(int(row["event_id"]))
        occ_start = str(row["occurrence_start_utc"])
        duration = event.end_dt_utc - event.start_dt_utc
        if duration.total_seconds() <= 0:
            duration = timedelta(hours=1)
        if not new_end or new_end <= new_start:
            new_end = new_start + duration

        if event.is_recurring:
            self.store.set_occurrence_override(
                event_id=event.id,
                occurrence_start_utc=occ_start,
                status="rescheduled",
                rescheduled_start_utc=new_start.isoformat(),
                rescheduled_end_utc=new_end.isoformat(),
            )
        else:
            self.store.update_event_fields(
                event.id,
                {"start_at_utc": new_start.isoformat(), "end_at_utc": new_end.isoformat()},
            )
        self._clear_pending("pending_reschedule")
        self.store.set("last_event_id", str(event.id))
        lines = [
            f"Rescheduled #E{event.id} {event.title}",
            f"New time: {new_start.astimezone(self.tz).strftime('%Y-%m-%d %I:%M %p')} -> "
            f"{new_end.astimezone(self.tz).strftime('%Y-%m-%d %I:%M %p')}",
        ]
        course_line = format_course_line(event.category, event.course_number)
        if course_line:
            lines.append(course_line)
        lines.append(f"Where: {event.location or 'none'}")
        self.telegram.send_message("\n".join(lines))
        return True

    def _offsets(self, event: Event) -> list[int]:
        return [1440, 720, 180, 60] if event.is_important else [180, 60]

    def _reminder_keyboard(self, event_id: int, occurrence_start_utc: str) -> dict[str, Any]:
        token = self.store.ensure_action_token(event_id, occurrence_start_utc)
        return {
            "inline_keyboard": [
                [{"text": "Done", "callback_data": f"d:{token}"}],
                [
                    {"text": "Snooze 10m", "callback_data": f"s10:{token}"},
                    {"text": "Snooze 30m", "callback_data": f"s30:{token}"},
                    {"text": "Snooze 1h", "callback_data": f"s60:{token}"},
                ],
                [{"text": "Reschedule", "callback_data": f"r:{token}"}],
            ]
        }
    def _process_callback(self, callback: dict[str, Any]) -> None:
        callback_id = str(callback.get("id", ""))
        data = str(callback.get("data", ""))
        message = callback.get("message") or {}
        chat_id = str((message.get("chat") or {}).get("id", ""))
        message_id = int(message.get("message_id", 0))

        if chat_id != self.config.telegram_chat_id:
            if callback_id:
                self.telegram.answer_callback_query(callback_id, "Unauthorized")
            return

        match = re.fullmatch(r"([a-z0-9]+):([a-f0-9]{16})", data)
        if not match:
            self.telegram.answer_callback_query(callback_id, "Invalid action")
            return
        action, token = match.group(1), match.group(2)
        row = self.store.get_action_token(token)
        if not row:
            self.telegram.answer_callback_query(callback_id, "Action expired")
            return

        event = self.store.get_event(int(row["event_id"]))
        occ_start = str(row["occurrence_start_utc"])

        if action == "d":
            if event.is_recurring:
                self.store.set_occurrence_override(event_id=event.id, occurrence_start_utc=occ_start, status="done")
            else:
                self.store.update_event_fields(event.id, {"status": "done"})
            self.telegram.answer_callback_query(callback_id, "Marked done")
            try:
                self.telegram.edit_reply_markup(chat_id, message_id, None)
            except Exception:
                logging.exception("Failed to clear keyboard")
            return

        if action in {"s10", "s30", "s60"}:
            minutes = int(action[1:])
            now = utc_now()
            due = now + timedelta(minutes=minutes)
            target_start = parse_iso_utc(occ_start)
            if due >= target_start:
                due = target_start - timedelta(minutes=1)
            if due <= now:
                due = now + timedelta(minutes=1)
            self.store.create_snooze(event.id, occ_start, due.isoformat())
            self.telegram.answer_callback_query(callback_id, f"Snoozed {minutes}m")
            return

        if action == "r":
            self._save_pending("pending_reschedule", {"token": token})
            self.telegram.answer_callback_query(callback_id, "Send new datetime")
            self.telegram.send_message(f"Send new datetime for #E{event.id} {event.title}. Example: tomorrow 3pm")
            return

        self.telegram.answer_callback_query(callback_id, "Unsupported")

    def run_reminder_scan_once(self) -> None:
        try:
            now = utc_now()
            soon = now + timedelta(hours=26)
            for event in self.store.list_active_events():
                occs = expand_occurrences(
                    event,
                    start_utc=now - timedelta(minutes=5),
                    end_utc=soon,
                    overrides=self.store.get_overrides_for_event(event.id),
                    max_items=220,
                )
                for occ in occs:
                    if occ.start_at_utc <= now:
                        continue
                    due_offsets = []
                    for off in self._offsets(event):
                        if occ.start_at_utc - timedelta(minutes=off) <= now < occ.start_at_utc:
                            due_offsets.append(off)
                    if not due_offsets:
                        continue
                    chosen = max(due_offsets)
                    if not self.store.mark_reminder_sent(event.id, occ.source_occurrence_start_utc.isoformat(), chosen):
                        continue
                    lines = [
                        f"Reminder ({chosen // 60}h before)",
                        f"#E{event.id} | {event.title}",
                    ]
                    course_line = format_course_line(event.category, event.course_number)
                    if course_line:
                        lines.append(course_line)
                    lines.extend(
                        [
                            f"When: {occ.start_at_utc.astimezone(self.tz).strftime('%Y-%m-%d %I:%M %p')} -> "
                            f"{occ.end_at_utc.astimezone(self.tz).strftime('%Y-%m-%d %I:%M %p')}",
                            f"Where: {event.location or 'none'}",
                            f"Type: {'IMPORTANT' if event.is_important else 'NORMAL'}",
                        ]
                    )
                    msg = "\n".join(lines)
                    self.telegram.send_message(
                        msg,
                        reply_markup=self._reminder_keyboard(event.id, occ.source_occurrence_start_utc.isoformat()),
                    )

            for row in self.store.pop_due_snoozes(now.isoformat()):
                event = self.store.get_event(int(row["event_id"]))
                occ_dt = parse_iso_utc(str(row["occurrence_start_utc"]))
                if occ_dt < now - timedelta(hours=1):
                    continue
                lines = [
                    "Snoozed reminder",
                    f"#E{event.id} | {event.title}",
                ]
                course_line = format_course_line(event.category, event.course_number)
                if course_line:
                    lines.append(course_line)
                lines.extend(
                    [
                        f"Start: {occ_dt.astimezone(self.tz).strftime('%Y-%m-%d %I:%M %p')}",
                        f"Where: {event.location or 'none'}",
                    ]
                )
                self.telegram.send_message(
                    "\n".join(lines),
                    reply_markup=self._reminder_keyboard(event.id, str(row["occurrence_start_utc"])),
                )
        except Exception:
            logging.exception("Reminder scan failed")

    def run_cleanup_once(self) -> None:
        try:
            self.store.cleanup_history(utc_now() - timedelta(days=180))
        except Exception:
            logging.exception("Cleanup failed")

    def _send_help(self) -> None:
        self.telegram.send_message(
            "Schedule commands:\n"
            "/list - upcoming schedule\n"
            "/history - expired history (30 days)\n"
            "/history <days> - max 180\n"
            "/status - running status\n"
            "/help - command list\n"
            "/confirm - confirm pending image extraction\n"
            "/confirm_clear_all - confirm deleting all saved schedule data\n"
            "/cancel - cancel pending image extraction\n"
            "Natural language (EN/ZH) works for add/edit/delete.\n"
            "Schedules are grouped into Submission and Upcoming Schedule.\n"
            "You can set a course number for submissions and edit it with natural language.\n"
            "Default category is upcoming. Default location is none. Default course number is none.\n"
            "Bulk updates are supported, for example: update all from E1 to E6 to course number CC0006.\n"
            "You can also say clear all schedules, and I will ask for a safety confirmation before deleting everything.\n"
            "You can also send an image (calendar/screenshot) and I will extract schedules then ask for confirmation."
        )

    def _mime_type_from_path(self, file_path: str) -> str:
        lower = file_path.lower()
        if lower.endswith(".png"):
            return "image/png"
        if lower.endswith(".webp"):
            return "image/webp"
        return "image/jpeg"

    def _handle_photo_message(self, photos: list[dict[str, Any]], caption: str) -> None:
        if not photos:
            return
        best = sorted(photos, key=lambda p: int(p.get("file_size") or 0))[-1]
        file_id = str(best.get("file_id", "")).strip()
        if not file_id:
            self.telegram.send_message("Could not read the photo file id.")
            return
        try:
            file_path = self.telegram.get_file_path(file_id)
            image_bytes = self.telegram.download_file_bytes(file_path)
            parsed = self.analyzer.extract_schedules_from_image(
                image_bytes=image_bytes,
                mime_type=self._mime_type_from_path(file_path),
                now_local_iso=datetime.now(self.tz).isoformat(),
                tz_name=self.config.timezone_name,
                caption=caption,
            )
        except Exception:
            logging.exception("Photo schedule extraction failed")
            self.telegram.send_message("I could not extract schedule from this image. Please try a clearer image.")
            return

        raw_events = parsed.get("events", [])
        if not isinstance(raw_events, list):
            raw_events = []
        normalized_events: list[dict[str, Any]] = []
        for item in raw_events[:12]:
            if not isinstance(item, dict):
                continue
            candidate = self._normalize_create_payload(item)
            title = str(candidate.get("title", "")).strip()
            start_local = str(candidate.get("start_local", "")).strip()
            if not title or not start_local:
                continue
            normalized_events.append(candidate)

        if not normalized_events:
            self.telegram.send_message(
                "No clear schedule item found in this image. You can resend a clearer image or type the schedule in text."
            )
            return

        self._save_pending(
            "pending_image_confirmation",
            {
                "events": normalized_events,
                "notes": str(parsed.get("notes", "")).strip()[:500],
                "created_at_utc": utc_now().isoformat(),
            },
        )

        lines = [
            "Image Extraction Preview",
            "Reply `confirm` to save all items, or `cancel` to discard.",
            "",
        ]
        for idx, item in enumerate(normalized_events, start=1):
            lines.append(self._format_create_preview(item, idx))
        notes = str(parsed.get("notes", "")).strip()
        if notes:
            lines.append(f"Notes: {notes[:250]}")
        self.telegram.send_message("\n".join(lines)[:3900])

    def _handle_create(self, create_data: dict[str, Any], raw_text: str, notify: bool = True) -> Event | None:
        payload = self._normalize_create_payload(create_data)
        title = str(payload.get("title", "")).strip()
        if not title:
            if notify:
                self.telegram.send_message("Please provide a title for the event.")
            return None
        start = parse_local_flexible_to_utc(str(payload.get("start_local", "")).strip(), self.tz)
        if not start:
            if notify:
                self.telegram.send_message("Cannot parse start time. Please send a clearer datetime.")
            return None
        end = parse_local_flexible_to_utc(str(payload.get("end_local", "")).strip(), self.tz)
        if not end or end <= start:
            end = start + timedelta(hours=1)

        is_important = to_bool(payload.get("is_important"), default=False)
        is_recurring = to_bool(payload.get("is_recurring"), default=False)
        location = str(payload.get("location", "none")).strip() or "none"
        category = normalize_category(payload.get("category"), title, payload.get("description", ""), raw_text)
        course_number = normalize_course_number(payload.get("course_number"), title, payload.get("description", ""), raw_text)
        recurrence: dict[str, Any] = {}
        if is_recurring:
            recurrence = self._build_recurrence(payload.get("recurrence"), start)
            if not recurrence:
                is_recurring = False

        event = self.store.create_event(
            title=title,
            description=str(payload.get("description", "")).strip(),
            location=location,
            category=category,
            course_number=course_number,
            start_at_utc=start.isoformat(),
            end_at_utc=end.isoformat(),
            timezone_name=self.config.timezone_name,
            is_important=is_important,
            is_recurring=is_recurring,
            recurrence_rule=recurrence,
            source_text=raw_text,
        )
        self.store.set("last_event_id", str(event.id))
        if notify:
            repeat = recurrence_text(event.recurrence_rule) if event.is_recurring else "none"
            lines = [
                f"Saved #E{event.id} | {event.title}",
                f"Category: {category_label(event.category)}",
            ]
            course_line = format_course_line(event.category, event.course_number)
            if course_line:
                lines.append(course_line)
            lines.extend(
                [
                    f"When: {fmt_local(event.start_at_utc, self.tz)} -> {fmt_local(event.end_at_utc, self.tz)}",
                    f"Where: {event.location or 'none'}",
                    f"Type: {'IMPORTANT' if event.is_important else 'NORMAL'} | Repeat: {repeat}",
                ]
            )
            msg = "\n".join(lines)
            self.telegram.send_message(msg)
        return event

    def _handle_nl(self, text: str) -> None:
        if self._handle_pending_clear_all(text):
            return
        if self._looks_like_clear_all_request(text):
            self._request_clear_all()
            return
        if self._handle_pending_image_confirmation(text):
            return
        if self._handle_pending_reschedule(text):
            return
        if self._handle_pending_selection(text):
            return

        parsed = self.analyzer.interpret_message(
            text=text,
            now_local_iso=datetime.now(self.tz).isoformat(),
            tz_name=self.config.timezone_name,
            sample_events=self._upcoming_samples(),
        )
        intent = str(parsed.get("intent", "unknown")).strip().lower()
        quick_changes: dict[str, Any] = {}
        quick_recur = self._extract_recurrence_change(text)
        quick_category = self._extract_category_change(text)
        quick_course = self._extract_course_number_change(text)
        if quick_recur:
            quick_changes.update(quick_recur)
        if quick_category:
            quick_changes.update(quick_category)
        if quick_course:
            quick_changes.update(quick_course)
        bulk_ids = self._extract_bulk_target_ids(text)
        target_query = str(parsed.get("target_query", "")).strip()

        if quick_changes:
            if bulk_ids:
                self._resolve_bulk_and_apply("update", bulk_ids, quick_changes)
                return
            eid_match = re.search(r"\bE(\d+)\b", text.upper())
            if eid_match:
                target_query = f"E{eid_match.group(1)}"
            if target_query:
                self._resolve_and_apply("update", target_query, quick_changes)
            else:
                self._request_selection_without_query("update", quick_changes)
            return

        if intent == "help":
            self._send_help()
            return
        if intent == "clear_all":
            self._request_clear_all()
            return
        if intent == "list_upcoming":
            self._send_upcoming()
            return
        if intent == "list_history":
            try:
                days = int(parsed.get("history_days", 30))
            except Exception:
                days = 30
            self._send_history(days)
            return
        if intent == "create":
            create_data = parsed.get("create")
            self._handle_create(create_data if isinstance(create_data, dict) else {}, text)
            return
        if intent in {"update", "delete", "mark_important", "mark_normal"}:
            changes = parsed.get("changes")
            parsed_changes = changes if isinstance(changes, dict) else {}
            if bulk_ids:
                self._resolve_bulk_and_apply(intent, bulk_ids, parsed_changes)
                return
            if target_query:
                self._resolve_and_apply(intent, target_query, parsed_changes)
                return
            self._request_selection_without_query(intent, parsed_changes)
            return

        self.telegram.send_message(
            "I could not classify this request. Try: add meeting tomorrow 2pm at office, show upcoming, show history, change E12 recurring to daily, delete E5, or clear all schedules."
        )

    def process_updates_once(self) -> None:
        try:
            offset = int(self.store.get("telegram_offset", "0"))
            updates = self.telegram.get_updates(offset=offset, timeout_sec=2)
            for upd in updates:
                next_offset = int(upd.get("update_id", 0)) + 1
                self.store.set("telegram_offset", str(next_offset))

                callback = upd.get("callback_query")
                if callback:
                    self._process_callback(callback)
                    continue

                message = upd.get("message") or {}
                chat_id = str((message.get("chat") or {}).get("id", ""))
                if chat_id != self.config.telegram_chat_id:
                    continue
                raw_text = (message.get("text") or "").strip()
                caption = (message.get("caption") or "").strip()
                photos = message.get("photo") or []

                if photos:
                    self._handle_photo_message(photos if isinstance(photos, list) else [], caption)
                    continue
                if not raw_text:
                    continue

                if raw_text.startswith("/start"):
                    self.telegram.send_message("Schedule agent ready. Use /help or natural language.")
                elif raw_text.startswith("/help"):
                    self._send_help()
                elif raw_text.startswith("/confirm_clear_all"):
                    if not self._handle_pending_clear_all("/confirm_clear_all"):
                        self.telegram.send_message("No pending clear-all request.")
                elif raw_text.startswith("/confirm"):
                    if not self._handle_pending_clear_all("/confirm"):
                        if not self._handle_pending_image_confirmation("confirm"):
                            self.telegram.send_message("No pending confirmation.")
                elif raw_text.startswith("/cancel"):
                    if not self._handle_pending_clear_all("/cancel"):
                        if not self._handle_pending_image_confirmation("cancel"):
                            if not self._handle_pending_selection("cancel"):
                                if not self._handle_pending_reschedule("cancel"):
                                    self.telegram.send_message("Nothing pending to cancel.")
                elif raw_text.startswith("/list"):
                    self._send_upcoming()
                elif raw_text.startswith("/history"):
                    parts = raw_text.split(maxsplit=1)
                    days = 30
                    if len(parts) == 2:
                        try:
                            days = int(parts[1].strip())
                        except Exception:
                            days = 30
                    self._send_history(days)
                elif raw_text.startswith("/status"):
                    self.telegram.send_message(
                        f"Running. timezone={self.config.timezone_name} poll={self.config.command_poll_seconds}s reminder_scan={self.config.reminder_scan_seconds}s"
                    )
                elif raw_text.startswith("/"):
                    self.telegram.send_message("Unknown command. Use /help.")
                else:
                    self._handle_nl(raw_text)
        except Exception:
            logging.exception("Update polling failed")

    def print_chat_ids(self) -> None:
        updates = self.telegram.get_updates(timeout_sec=3)
        if not updates:
            print("No updates found. Send /start to your bot, then run this again.")
            return
        seen = set()
        for upd in updates:
            msg = upd.get("message") or {}
            chat = msg.get("chat") or {}
            cid = str(chat.get("id", ""))
            if cid and cid not in seen:
                seen.add(cid)
                print(f"chat_id={cid} chat_type={chat.get('type')} title={chat.get('title', '')}")

    def serve(self) -> None:
        self.scheduler.add_job(
            self.process_updates_once,
            trigger="interval",
            seconds=self.config.command_poll_seconds,
            id="telegram_poll",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_reminder_scan_once,
            trigger="interval",
            seconds=self.config.reminder_scan_seconds,
            id="reminder_scan",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_cleanup_once,
            trigger="cron",
            hour=self.config.cleanup_hour_local,
            minute=0,
            id="cleanup",
            replace_existing=True,
        )
        self.scheduler.start()
        try:
            self.telegram.send_message("Schedule tracking agent is running. Use /help or send natural language (EN/ZH).")
        except Exception:
            logging.exception("Startup message failed; bot will keep running and retry on next updates")
        try:
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            pass
        finally:
            self.scheduler.shutdown(wait=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram schedule tracking agent")
    parser.add_argument("--commands-once", action="store_true", help="Poll updates once")
    parser.add_argument("--reminders-once", action="store_true", help="Run reminder scan once")
    parser.add_argument("--cleanup-once", action="store_true", help="Run history cleanup once")
    parser.add_argument("--get-chat-id", action="store_true", help="Print chat ids from updates")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    args = parse_args()

    if args.get_chat_id:
        partial = load_partial_config()
        if not partial.telegram_bot_token:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in .env")
        telegram = TelegramClient(partial.telegram_bot_token, partial.telegram_chat_id or "0")
        updates = telegram.get_updates(timeout_sec=3)
        if not updates:
            print("No updates found. Send /start to your bot, then run this again.")
            return 0
        seen = set()
        for upd in updates:
            msg = upd.get("message") or {}
            chat = msg.get("chat") or {}
            cid = str(chat.get("id", ""))
            if cid and cid not in seen:
                seen.add(cid)
                print(f"chat_id={cid} chat_type={chat.get('type')} title={chat.get('title', '')}")
        return 0

    config = load_config()
    agent = Agent(config)
    if args.commands_once:
        agent.process_updates_once()
        return 0
    if args.reminders_once:
        agent.run_reminder_scan_once()
        return 0
    if args.cleanup_once:
        agent.run_cleanup_once()
        return 0
    agent.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



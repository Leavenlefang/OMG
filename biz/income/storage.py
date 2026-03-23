"""
SQLite storage for daily income snapshots.
Stores every run so you can compare today vs yesterday vs last week.
"""

import json
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from .platforms.base import DailySummary

DB_PATH = Path(__file__).parent.parent / "data" / "income.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_income (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,          -- YYYY-MM-DD
                platform    TEXT NOT NULL,
                revenue     REAL NOT NULL,
                orders      INTEGER NOT NULL,
                top_items   TEXT,                   -- JSON
                pending     TEXT,                   -- JSON
                alerts      TEXT,                   -- JSON
                is_mock     INTEGER DEFAULT 0,
                error       TEXT,
                fetched_at  TEXT NOT NULL,
                UNIQUE(date, platform)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_date ON daily_income(date)
        """)


def upsert(summary: DailySummary):
    today = date.today().isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO daily_income
                (date, platform, revenue, orders, top_items, pending, alerts, is_mock, error, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, platform) DO UPDATE SET
                revenue    = excluded.revenue,
                orders     = excluded.orders,
                top_items  = excluded.top_items,
                pending    = excluded.pending,
                alerts     = excluded.alerts,
                is_mock    = excluded.is_mock,
                error      = excluded.error,
                fetched_at = excluded.fetched_at
        """, (
            today,
            summary.platform,
            summary.revenue,
            summary.orders,
            json.dumps(summary.top_items, ensure_ascii=False),
            json.dumps(summary.pending_actions, ensure_ascii=False),
            json.dumps(summary.alerts, ensure_ascii=False),
            1 if summary.is_mock else 0,
            summary.error,
            summary.fetched_at.isoformat(),
        ))


def get_day(target_date: date) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_income WHERE date = ?",
            (target_date.isoformat(),)
        ).fetchall()
    return [dict(r) for r in rows]


def get_totals(target_date: date) -> dict:
    """Returns {revenue, orders, by_platform} for a given date."""
    rows = get_day(target_date)
    total_revenue = sum(r["revenue"] for r in rows if not r["error"])
    total_orders  = sum(r["orders"]  for r in rows if not r["error"])
    by_platform   = {r["platform"]: {"revenue": r["revenue"], "orders": r["orders"]} for r in rows}
    return {"revenue": total_revenue, "orders": total_orders, "by_platform": by_platform}


def get_yesterday_totals() -> dict:
    return get_totals(date.today() - timedelta(days=1))


def get_today_totals() -> dict:
    return get_totals(date.today())


def get_pending_actions() -> list[str]:
    rows = get_day(date.today())
    actions = []
    for r in rows:
        pending = json.loads(r["pending"] or "[]")
        for p in pending:
            actions.append(f"[{r['platform']}] {p}")
    return actions


def get_top_items_today() -> list[dict]:
    """Aggregated top items across all platforms today."""
    rows = get_day(date.today())
    combined: dict[str, int] = {}
    for r in rows:
        items = json.loads(r["top_items"] or "[]")
        for item in items:
            name = item.get("name", "?")
            qty  = item.get("qty", 0)
            combined[name] = combined.get(name, 0) + qty
    return sorted(
        [{"name": k, "qty": v} for k, v in combined.items()],
        key=lambda x: x["qty"],
        reverse=True,
    )[:5]

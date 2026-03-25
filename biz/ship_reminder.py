#!/usr/bin/env python3
"""
Shopee ship reminder — runs at 14:00 daily.

Checks for unshipped Shopee orders and sends a LINE alert if > 0.
Per CLAUDE.md: ⚡ Action required when unshipped > 5.

Usage:
  python3 biz/ship_reminder.py           # check + send LINE if needed
  python3 biz/ship_reminder.py --preview # print without sending
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from biz.income import storage


CONFIG_PATH = Path(__file__).parent / "config.yaml"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def get_unshipped_count() -> int:
    """Get count of unshipped Shopee orders from today's data."""
    from datetime import date
    rows = storage.get_day(date.today())

    for row in rows:
        if row["platform"] == "Shopee":
            # Look for shipping-related pending actions
            pending = row.get("pending_actions", [])
            if isinstance(pending, str):
                import json
                try:
                    pending = json.loads(pending)
                except (json.JSONDecodeError, TypeError):
                    pending = [pending]

            for action in pending:
                if isinstance(action, str) and "ship" in action.lower():
                    # Extract number from strings like "3 orders ready to ship"
                    import re
                    match = re.search(r"(\d+)", action)
                    if match:
                        return int(match.group(1))
            return 0
    return 0


def build_reminder(count: int) -> str:
    """Build the LINE reminder message."""
    if count == 0:
        return ""

    lines = []
    if count > 5:
        lines.append(f"⚡ Shopee 有 {count} 筆待出貨！趕快處理！")
    else:
        lines.append(f"📦 Shopee 有 {count} 筆待出貨")

    lines.append("")
    lines.append("記得今天出貨喔 💪")
    lines.append("")
    lines.append("OMG Coffee ☕")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Shopee ship reminder")
    parser.add_argument("--preview", action="store_true", help="Print without sending")
    args = parser.parse_args()

    count = get_unshipped_count()

    if count == 0:
        print("✅ No unshipped Shopee orders. Nothing to send.")
        return

    message = build_reminder(count)

    if args.preview:
        print(message)
        return

    print(message)
    print()

    config = _load_config()
    token = config.get("line_notify", {}).get("token", "")

    if not token:
        print("⚠️  LINE Notify token not set. Message printed above only.")
        return

    from biz.brief import line_notify
    line_notify.send(token, message)
    print("✅ Ship reminder sent to LINE.")


if __name__ == "__main__":
    main()

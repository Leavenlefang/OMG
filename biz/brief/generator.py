"""
Daily brief generator.
Pulls from SQLite storage and formats a LINE message.
"""

from datetime import date, timedelta
from pathlib import Path

import yaml

from ..income import storage

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def _fmt_revenue(amount: float) -> str:
    return f"NT${amount:,.0f}"


def _delta(today: float, yesterday: float) -> str:
    if yesterday == 0:
        return ""
    diff = today - yesterday
    pct  = (diff / yesterday) * 100
    arrow = "↑" if diff >= 0 else "↓"
    return f" {arrow}{abs(pct):.0f}%"


def build() -> str:
    today     = date.today()
    yesterday = today - timedelta(days=1)

    today_totals     = storage.get_today_totals()
    yesterday_totals = storage.get_yesterday_totals()
    pending          = storage.get_pending_actions()
    top_items        = storage.get_top_items_today()
    today_rows       = storage.get_day(today)

    total_rev   = today_totals["revenue"]
    total_ord   = today_totals["orders"]
    yest_rev    = yesterday_totals["revenue"]
    by_platform = today_totals["by_platform"]

    # ── Header ──
    lines = [
        f"\n☀️ 早安！{today.strftime('%m/%d')} 日報",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    # ── Total revenue ──
    delta = _delta(total_rev, yest_rev)
    lines.append(f"💰 今日營收：{_fmt_revenue(total_rev)}{delta}")
    lines.append(f"📦 今日訂單：{total_ord} 筆")
    lines.append("")

    # ── Per-platform breakdown ──
    lines.append("📊 各平台：")
    platform_icons = {
        "iChef":     "🍽",
        "Uber Eats": "🛵",
        "Shopee":    "🛒",
        "EasyStore": "🌐",
    }
    for row in today_rows:
        if row.get("error"):
            icon = platform_icons.get(row["platform"], "•")
            lines.append(f"  {icon} {row['platform']}: ⚠️ 連線失敗")
        else:
            icon = platform_icons.get(row["platform"], "•")
            mock_tag = " [模擬]" if row.get("is_mock") else ""
            lines.append(
                f"  {icon} {row['platform']}: {_fmt_revenue(row['revenue'])} / {row['orders']} 筆{mock_tag}"
            )

    # ── Top items ──
    if top_items:
        lines.append("")
        lines.append("🏆 今日熱銷：")
        for item in top_items[:3]:
            lines.append(f"  • {item['name']} × {item['qty']}")

    # ── Pending actions ──
    if pending:
        lines.append("")
        lines.append("⚡ 待處理：")
        for action in pending[:5]:
            lines.append(f"  • {action}")

    # ── Footer ──
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("Go get 'em ☕")

    return "\n".join(lines)


def send_brief():
    config = _load_config()
    token  = config.get("line_notify", {}).get("token", "")

    message = build()
    print(message)
    print()

    if not token:
        print("⚠️  LINE Notify token not set. Message printed above only.")
        print("   Add it to config.yaml → line_notify.token")
        return

    from . import line_notify
    line_notify.send(token, message)
    print("✅ Sent to LINE.")

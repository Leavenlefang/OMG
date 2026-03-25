"""
Daily brief generator.
Pulls from SQLite storage, runs rules engine, formats a LINE message.

Two-phase approach (inspired by CLAUDE.md):
  Phase 1 — Rules engine classifies data: flags, alerts, clean items
  Phase 2 — Brief formats results: critical items first, then normal data
"""

from datetime import date, timedelta
from pathlib import Path

import yaml

from ..income import storage
from ..income import rules_engine

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

PLATFORM_ICONS = {
    "iChef":     "🍽",
    "Uber Eats": "🛵",
    "Shopee":    "🛒",
    "EasyStore": "🌐",
}


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def _fmt(amount: float) -> str:
    return f"NT${amount:,.0f}"


def _delta(today: float, yesterday: float) -> str:
    if yesterday == 0:
        return ""
    diff = today - yesterday
    pct  = (diff / yesterday) * 100
    arrow = "↑" if diff >= 0 else "↓"
    return f" {arrow}{abs(pct):.0f}%"


def build(summaries: list = None) -> str:
    today     = date.today()
    yesterday = today - timedelta(days=1)

    today_totals     = storage.get_today_totals()
    yesterday_totals = storage.get_yesterday_totals()
    pending          = storage.get_pending_actions()
    top_items        = storage.get_top_items_today()
    today_rows       = storage.get_day(today)
    unresolved       = rules_engine.load_review_queue()

    total_rev = today_totals["revenue"]
    total_ord = today_totals["orders"]
    yest_rev  = yesterday_totals["revenue"]

    # Phase 1: Run rules engine if we have fresh summaries
    rules_result = None
    if summaries:
        rules_result = rules_engine.evaluate(summaries, today_totals)
        rules_engine.save_review_queue(rules_result.flags + rules_result.alerts)

    lines = []

    # ── Header ──
    status_icon = "🔴" if (rules_result and rules_result.has_critical) else "☀️"
    lines.append(f"\n{status_icon} 早安！{today.strftime('%m/%d')} 日報")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    # ── Phase 1: Celebrations first ──
    if rules_result:
        for alert in rules_result.celebrations():
            lines.append(alert.message)

    # ── Phase 1: Critical flags (RED) — shown before anything else ──
    red_flags = rules_result.red_flags() if rules_result else []
    carryover  = [i for i in unresolved if i.get("severity") == "red"]
    all_red    = red_flags + carryover

    if all_red:
        lines.append("")
        lines.append("🚨 需要立即處理：")
        for flag in all_red:
            icon = PLATFORM_ICONS.get(flag.platform if hasattr(flag, "platform") else flag.get("platform", ""), "•")
            msg  = flag.message if hasattr(flag, "message") else flag.get("message", "")
            lines.append(f"  {icon} {msg}")

    # ── Revenue summary ──
    lines.append("")
    delta = _delta(total_rev, yest_rev)
    lines.append(f"💰 今日營收：{_fmt(total_rev)}{delta}")
    lines.append(f"📦 今日訂單：{total_ord} 筆")
    lines.append("")

    # ── Per-platform breakdown ──
    lines.append("📊 各平台：")
    for row in today_rows:
        icon = PLATFORM_ICONS.get(row["platform"], "•")
        if row.get("error"):
            lines.append(f"  {icon} {row['platform']}: ❌ 連線失敗")
        else:
            mock_tag = " [模擬]" if row.get("is_mock") else ""
            # Mark platforms with yellow flags
            yellow = rules_result and any(
                f.platform == row["platform"] for f in rules_result.yellow_flags()
            )
            flag_tag = " ⚠️" if yellow else ""
            lines.append(
                f"  {icon} {row['platform']}: {_fmt(row['revenue'])} / {row['orders']} 筆{mock_tag}{flag_tag}"
            )

    # ── Yellow flags (warnings) ──
    yellow_flags = rules_result.yellow_flags() if rules_result else []
    if yellow_flags:
        lines.append("")
        lines.append("⚠️ 注意事項：")
        for flag in yellow_flags:
            icon = PLATFORM_ICONS.get(flag.platform, "•")
            lines.append(f"  {icon} {flag.message}")

    # ── Non-critical alerts ──
    if rules_result:
        non_crit_alerts = [a for a in rules_result.alerts if a.severity not in ("red", "celebrate")]
        if non_crit_alerts:
            lines.append("")
            for alert in non_crit_alerts:
                lines.append(f"  {alert.message}")

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

    # ── Carryover review queue (non-red) ──
    carryover_yellow = [i for i in unresolved if i.get("severity") != "red"]
    if carryover_yellow:
        lines.append("")
        lines.append(f"📋 待確認事項 ({len(carryover_yellow)} 項)：")
        for item in carryover_yellow[:3]:
            icon = PLATFORM_ICONS.get(item.get("platform", ""), "•")
            lines.append(f"  {icon} [{item['date']}] {item['message']}")

    # ── Footer ──
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    if rules_result and rules_result.has_critical:
        lines.append("處理完再去衝咖啡 ☕")
    else:
        lines.append("Go get 'em ☕")

    return "\n".join(lines)


def build_eod() -> str:
    today     = date.today()
    yesterday = today - timedelta(days=1)

    today_totals     = storage.get_today_totals()
    yesterday_totals = storage.get_yesterday_totals()
    top_items        = storage.get_top_items_today()
    today_rows       = storage.get_day(today)
    unresolved       = rules_engine.load_review_queue()

    total_rev = today_totals["revenue"]
    total_ord = today_totals["orders"]
    yest_rev  = yesterday_totals["revenue"]

    lines = []

    # ── Header ──
    great_day = total_rev >= 20000
    header_icon = "🎉" if great_day else "🌙"
    lines.append(f"\n{header_icon} {today.strftime('%m/%d')} 收攤囉！")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    if great_day:
        lines.append("今天超棒！慶祝一下 🎊")
        lines.append("")

    # ── Day total ──
    delta = _delta(total_rev, yest_rev)
    lines.append(f"💰 今日總營收：{_fmt(total_rev)}{delta}")
    lines.append(f"📦 今日訂單：{total_ord} 筆")
    lines.append("")

    # ── Per-platform breakdown ──
    lines.append("📊 各平台結算：")
    for row in today_rows:
        icon = PLATFORM_ICONS.get(row["platform"], "•")
        if row.get("error"):
            lines.append(f"  {icon} {row['platform']}: ❌ 連線失敗")
        else:
            mock_tag = " [模擬]" if row.get("is_mock") else ""
            lines.append(
                f"  {icon} {row['platform']}: {_fmt(row['revenue'])} / {row['orders']} 筆{mock_tag}"
            )

    # ── Top items ──
    if top_items:
        lines.append("")
        lines.append("🏆 今日熱銷前三：")
        for item in top_items[:3]:
            lines.append(f"  • {item['name']} × {item['qty']}")

    # ── Unresolved review queue ──
    if unresolved:
        lines.append("")
        lines.append(f"📋 尚未處理 ({len(unresolved)} 項)：")
        for item in unresolved[:3]:
            icon = PLATFORM_ICONS.get(item.get("platform", ""), "•")
            lines.append(f"  {icon} {item['message']}")
        if len(unresolved) > 3:
            lines.append(f"  … 還有 {len(unresolved) - 3} 項")

    # ── Slow day alert ──
    if total_rev < 3000:
        lines.append("")
        lines.append("🔴 今天營收偏低，明天加油！")

    # ── Footer ──
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("明天見！OMG Coffee ☕")

    return "\n".join(lines)


def _line_send(message: str) -> bool:
    """Send a message via LINE Messaging API. Returns True if sent, False if not configured."""
    config        = _load_config()
    line_cfg      = config.get("line", {})
    channel_token = line_cfg.get("channel_token", "")
    user_id       = line_cfg.get("user_id", "")

    if not channel_token or not user_id:
        print("⚠️  LINE not configured. Message printed above only.")
        print("   Add channel_token + user_id to config.yaml → line")
        print("   See biz/setup/LINE_MESSAGING.md for setup steps.")
        return False

    from . import line_client
    line_client.send(channel_token, user_id, message)
    return True


def send_brief(summaries: list = None):
    message = build(summaries=summaries)
    print(message)
    print()

    if _line_send(message):
        print("✅ Sent to LINE.")


def send_eod():
    message = build_eod()
    print(message)
    print()

    if _line_send(message):
        print("✅ EOD summary sent to LINE.")

"""
rules_engine.py — Applies business rules from rules.yaml to income data.

This is the intelligence layer. Instead of blindly displaying numbers,
it classifies what's normal, what needs attention, and what must be
reviewed by a human before any action is taken.

Mirrors the two-phase classification described in CLAUDE.md Section 2.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

import yaml

from .platforms.base import DailySummary
from . import storage

RULES_PATH = Path(__file__).parent.parent / "rules.yaml"
REVIEW_QUEUE_PATH = Path(__file__).parent.parent / "data" / "review_queue.json"


def _load_rules() -> dict:
    if not RULES_PATH.exists():
        return {}
    with open(RULES_PATH) as f:
        return yaml.safe_load(f) or {}


@dataclass
class Flag:
    """A single flagged item requiring human attention."""
    rule_id: str
    platform: str
    severity: str          # "red" | "yellow" | "celebrate"
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False


@dataclass
class RulesResult:
    """Output of the rules engine for a day's data."""
    flags: list = field(default_factory=list)      # List[Flag]
    alerts: list = field(default_factory=list)     # List[Flag] (threshold-based)
    auto_ok: list = field(default_factory=list)    # platforms that passed all rules
    has_critical: bool = False

    def red_flags(self):
        return [f for f in self.flags if f.severity == "red"]

    def yellow_flags(self):
        return [f for f in self.flags if f.severity == "yellow"]

    def celebrations(self):
        return [f for f in self.alerts if f.severity == "celebrate"]


def evaluate(summaries: list, today_totals: dict) -> RulesResult:
    """
    Run all exclusion rules and alert thresholds against today's data.
    Returns a RulesResult with all flags raised.
    """
    rules  = _load_rules()
    result = RulesResult()

    total_revenue  = today_totals.get("revenue", 0)
    total_orders   = today_totals.get("orders", 0)
    by_platform    = today_totals.get("by_platform", {})
    current_hour   = datetime.now().hour

    # ── Exclusion rules (per-platform) ──
    exclusion_rules = rules.get("exclusion_rules", [])
    active_platforms = [s for s in summaries if not s.error and s.revenue > 0]

    for summary in summaries:
        for rule in exclusion_rules:
            cond = rule.get("condition")
            flag = None

            # EX1: Negative revenue
            if cond == "revenue_negative" and summary.revenue < 0:
                flag = Flag(
                    rule_id=rule["id"], platform=summary.platform,
                    severity=rule.get("severity", "red"),
                    message=rule["message"],
                )

            # EX3: API error
            elif cond == "has_error" and summary.error:
                flag = Flag(
                    rule_id=rule["id"], platform=summary.platform,
                    severity=rule.get("severity", "red"),
                    message=rule["message"],
                )

            # EX4: Revenue drop vs last week
            elif cond == "revenue_drop_vs_last_week":
                last_week = storage.get_totals(date.today() - timedelta(days=7))
                last_week_rev = last_week.get("by_platform", {}).get(summary.platform, {}).get("revenue", 0)
                if last_week_rev > 0 and summary.revenue > 0:
                    drop_pct = ((last_week_rev - summary.revenue) / last_week_rev) * 100
                    threshold = rule.get("threshold_pct", 50)
                    if drop_pct >= threshold:
                        msg = rule["message"].format(pct=drop_pct)
                        flag = Flag(
                            rule_id=rule["id"], platform=summary.platform,
                            severity=rule.get("severity", "yellow"),
                            message=msg,
                        )

            # EX5 + EX6: Zero orders during peak / platform discrepancy
            elif cond in ("zero_orders_during_peak", "one_platform_silent_others_active"):
                peak_windows = rule.get("peak_hours", [])
                in_peak = any(start <= current_hour < end for start, end in peak_windows)
                if in_peak and summary.orders == 0 and len(active_platforms) > 1:
                    msg = rule["message"].format(platform=summary.platform)
                    flag = Flag(
                        rule_id=rule["id"], platform=summary.platform,
                        severity=rule.get("severity", "yellow"),
                        message=msg,
                    )

            # EX7: Keyword in pending actions
            elif cond == "keyword_in_pending":
                keywords = rule.get("keywords", [])
                for action in summary.pending_actions:
                    if any(kw.lower() in action.lower() for kw in keywords):
                        flag = Flag(
                            rule_id=rule["id"], platform=summary.platform,
                            severity=rule.get("severity", "yellow"),
                            message=rule["message"],
                        )
                        break

            if flag:
                result.flags.append(flag)

        # Track clean platforms
        if not any(f.platform == summary.platform for f in result.flags):
            result.auto_ok.append(summary.platform)

    # ── Alert thresholds (total-level) ──
    alert_rules = rules.get("alerts", {})

    # Slow day
    slow_day = alert_rules.get("slow_day", {})
    if total_revenue < slow_day.get("threshold", 3000) and current_hour >= slow_day.get("by_hour", 15):
        hours_left = 21 - current_hour
        msg = slow_day.get("message", "").format(hours_left=hours_left, revenue=total_revenue)
        result.alerts.append(Flag(
            rule_id="AL1", platform="all",
            severity=slow_day.get("severity", "red"),
            message=msg,
        ))

    # Great day
    great_day = alert_rules.get("great_day", {})
    if total_revenue >= great_day.get("threshold", 20000):
        msg = great_day.get("message", "🎉 Great day!").format(revenue=total_revenue)
        result.alerts.append(Flag(
            rule_id="AL2", platform="all",
            severity="celebrate",
            message=msg,
        ))

    # Shopee unshipped
    shopee_rule = alert_rules.get("shopee_unshipped", {})
    pending = storage.get_pending_actions()
    ship_items = [p for p in pending if "ship" in p.lower() or "出貨" in p]
    if len(ship_items) >= shopee_rule.get("threshold", 5):
        msg = shopee_rule.get("message", "").format(count=len(ship_items))
        result.alerts.append(Flag(
            rule_id="AL3", platform="Shopee",
            severity=shopee_rule.get("severity", "yellow"),
            message=msg,
        ))

    result.has_critical = any(f.severity == "red" for f in result.flags + result.alerts)
    return result


def save_review_queue(flags: list):
    """Persist unresolved flags to review_queue.json."""
    REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing queue
    existing = []
    if REVIEW_QUEUE_PATH.exists():
        with open(REVIEW_QUEUE_PATH) as f:
            existing = json.load(f)

    # Add new unresolved flags (deduplicate by rule_id + platform + date)
    today_str = date.today().isoformat()
    existing_keys = {(e["rule_id"], e["platform"], e.get("date", "")) for e in existing if not e.get("resolved")}

    for flag in flags:
        key = (flag.rule_id, flag.platform, today_str)
        if key not in existing_keys:
            existing.append({
                "rule_id":   flag.rule_id,
                "platform":  flag.platform,
                "severity":  flag.severity,
                "message":   flag.message,
                "date":      today_str,
                "timestamp": flag.timestamp,
                "resolved":  False,
            })

    with open(REVIEW_QUEUE_PATH, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def load_review_queue() -> list:
    """Load all unresolved flags."""
    if not REVIEW_QUEUE_PATH.exists():
        return []
    with open(REVIEW_QUEUE_PATH) as f:
        items = json.load(f)
    return [i for i in items if not i.get("resolved")]


def resolve(rule_id: str, platform: str):
    """Mark a flag as resolved (called after human review)."""
    if not REVIEW_QUEUE_PATH.exists():
        return
    with open(REVIEW_QUEUE_PATH) as f:
        items = json.load(f)
    for item in items:
        if item["rule_id"] == rule_id and item["platform"] == platform:
            item["resolved"] = True
            item["resolved_at"] = datetime.now().isoformat()
    with open(REVIEW_QUEUE_PATH, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

"""
Message handler — triage incoming customer messages.

Implements CLAUDE.md Section 3:
  - Auto-reply: opening hours, menu/price, order status
  - Escalate: complaints, refunds, allergies, custom large orders
  - Language: match customer language (zh-TW default, EN if they write English)
  - Tone: warm, friendly, casual — sign off as OMG Coffee ☕
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

RULES_PATH = Path(__file__).parent.parent / "rules.yaml"
MENU_PATH = Path(__file__).parent.parent / "menu" / "menu.yaml"


class Action(Enum):
    AUTO_REPLY = "auto_reply"
    ESCALATE = "escalate"


@dataclass
class TriageResult:
    action: Action
    category: str           # e.g. "hours", "menu", "complaint", "refund"
    reply: Optional[str]    # auto-reply text, or None if escalated
    reason: str             # why this decision was made
    language: str           # "zh" or "en"


def _load_rules() -> dict:
    with open(RULES_PATH) as f:
        return yaml.safe_load(f).get("message_rules", {})


def _detect_language(text: str) -> str:
    """Simple heuristic: if mostly ASCII, it's English."""
    ascii_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    total_chars = sum(1 for c in text if c.isalpha()) or 1
    return "en" if ascii_chars / total_chars > 0.7 else "zh"


def _has_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


# ── Auto-reply templates ──

HOURS_ZH = (
    "嗨！我們的營業時間是每天 09:00–21:00 喔 ☀️\n"
    "歡迎來坐坐！\n\n"
    "OMG Coffee ☕"
)

HOURS_EN = (
    "Hi! We're open daily from 9:00 AM to 9:00 PM.\n"
    "Come visit us!\n\n"
    "OMG Coffee ☕"
)

MENU_ZH = (
    "嗨！這是我們目前的菜單：\n\n"
    "{menu_items}\n\n"
    "有任何問題歡迎問我們 😊\n\n"
    "OMG Coffee ☕"
)

MENU_EN = (
    "Hi! Here's our current menu:\n\n"
    "{menu_items}\n\n"
    "Let us know if you have any questions!\n\n"
    "OMG Coffee ☕"
)

ESCALATE_ZH = None  # escalated messages get no auto-reply
ESCALATE_EN = None


def _build_menu_snippet(lang: str) -> str:
    """Build a short menu listing from menu.yaml."""
    if not MENU_PATH.exists():
        return "（菜單更新中）" if lang == "zh" else "(Menu updating...)"

    with open(MENU_PATH) as f:
        data = yaml.safe_load(f)

    lines = []
    for item in (data or {}).get("items", []):
        if not item.get("in_stock", True):
            continue
        name = item["name_zh"] if lang == "zh" else item["name_en"]
        lines.append(f"• {name} — NT${item['base_price']}")
        if len(lines) >= 8:
            lines.append("...更多品項歡迎現場看" if lang == "zh" else "...and more!")
            break

    return "\n".join(lines)


def triage(message: str, source: str = "unknown") -> TriageResult:
    """
    Classify an incoming message and return a TriageResult.

    Args:
        message: the customer's text
        source:  platform/channel (e.g. "LINE", "Shopee", "Instagram")

    Returns:
        TriageResult with action, optional reply, and reasoning
    """
    rules = _load_rules()
    lang = _detect_language(message)
    escalate_kw = rules.get("always_escalate_keywords", [])

    # ── Step 1: Check for mandatory escalation keywords ──
    if _has_keyword(message, escalate_kw):
        matched = [kw for kw in escalate_kw if kw.lower() in message.lower()]
        return TriageResult(
            action=Action.ESCALATE,
            category="escalation_keyword",
            reply=None,
            reason=f"Contains escalation keyword(s): {', '.join(matched)}",
            language=lang,
        )

    # ── Step 2: Check for large/custom order mentions ──
    large_order_patterns = [
        r"(\d{2,})\s*[杯份個瓶包cups?items?]",  # "20杯", "15 cups"
        r"nt\$?\s*[3-9],?\d{3}",                   # NT$3,000+
        r"批發|wholesale|團購|group\s*order",
    ]
    for pattern in large_order_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return TriageResult(
                action=Action.ESCALATE,
                category="large_order",
                reply=None,
                reason=f"Possible large/custom order (matched: {pattern})",
                language=lang,
            )

    # ── Step 3: Auto-reply — opening hours ──
    hours_keywords = ["幾點", "營業", "開門", "關門", "幾時", "open", "hours", "close",
                      "what time", "when do you"]
    if _has_keyword(message, hours_keywords):
        return TriageResult(
            action=Action.AUTO_REPLY,
            category="hours",
            reply=HOURS_EN if lang == "en" else HOURS_ZH,
            reason="Opening hours enquiry",
            language=lang,
        )

    # ── Step 4: Auto-reply — menu / price ──
    menu_keywords = ["菜單", "menu", "價格", "price", "多少錢", "how much", "什麼飲料",
                     "what do you serve", "品項"]
    if _has_keyword(message, menu_keywords):
        snippet = _build_menu_snippet(lang)
        template = MENU_EN if lang == "en" else MENU_ZH
        return TriageResult(
            action=Action.AUTO_REPLY,
            category="menu",
            reply=template.format(menu_items=snippet),
            reason="Menu/price enquiry",
            language=lang,
        )

    # ── Step 5: Auto-reply — order status ──
    status_keywords = ["訂單", "出貨", "寄了嗎", "到了嗎", "order status", "shipped",
                       "tracking", "where is my"]
    if _has_keyword(message, status_keywords):
        reply_zh = "收到！我幫你查一下訂單狀態，稍等一下喔 😊\n\nOMG Coffee ☕"
        reply_en = "Got it! Let me check your order status. One moment please!\n\nOMG Coffee ☕"
        return TriageResult(
            action=Action.AUTO_REPLY,
            category="order_status",
            reply=reply_en if lang == "en" else reply_zh,
            reason="Order status enquiry",
            language=lang,
        )

    # ── Step 6: No match — escalate to human for safety ──
    return TriageResult(
        action=Action.ESCALATE,
        category="unclassified",
        reply=None,
        reason="Message doesn't match any auto-reply pattern; escalating to human",
        language=lang,
    )

"""Tests for the message handler."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from biz.messages.handler import triage, Action


class TestEscalation:
    """Messages containing escalation keywords must ALWAYS be escalated."""

    @pytest.mark.parametrize("msg", [
        "我要退款",
        "I want a refund please",
        "客訴，你們的咖啡太難喝",
        "I have an allergy to nuts",
        "過敏原有哪些？我對花生過敏",
        "This is a complaint about my order",
    ])
    def test_escalation_keywords(self, msg):
        result = triage(msg)
        assert result.action == Action.ESCALATE
        assert result.reply is None

    def test_large_order_escalated(self):
        result = triage("我想訂20杯拿鐵")
        assert result.action == Action.ESCALATE
        assert result.category == "large_order"

    def test_wholesale_escalated(self):
        result = triage("想問批發價格")
        assert result.action == Action.ESCALATE


class TestAutoReply:
    """Auto-reply patterns should return a reply and not escalate."""

    def test_hours_chinese(self):
        result = triage("請問你們幾點開門？")
        assert result.action == Action.AUTO_REPLY
        assert result.category == "hours"
        assert "09:00" in result.reply
        assert "OMG Coffee" in result.reply

    def test_hours_english(self):
        result = triage("What time do you open?")
        assert result.action == Action.AUTO_REPLY
        assert result.category == "hours"
        assert "9:00 AM" in result.reply

    def test_menu_chinese(self):
        result = triage("有菜單嗎？")
        assert result.action == Action.AUTO_REPLY
        assert result.category == "menu"

    def test_menu_english(self):
        result = triage("Can I see the menu?")
        assert result.action == Action.AUTO_REPLY
        assert result.category == "menu"
        assert "NT$" in result.reply

    def test_order_status(self):
        result = triage("我的訂單寄了嗎？")
        assert result.action == Action.AUTO_REPLY
        assert result.category == "order_status"


class TestLanguageDetection:
    def test_chinese_detected(self):
        result = triage("你們幾點開門")
        assert result.language == "zh"

    def test_english_detected(self):
        result = triage("What are your opening hours?")
        assert result.language == "en"


class TestUnclassified:
    def test_random_message_escalated(self):
        """Unknown messages should be escalated for safety."""
        result = triage("今天天氣真好")
        assert result.action == Action.ESCALATE
        assert result.category == "unclassified"

"""Tests for the Shopee ship reminder."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from biz.ship_reminder import build_reminder


class TestBuildReminder:
    def test_zero_unshipped_returns_empty(self):
        assert build_reminder(0) == ""

    def test_low_count_normal_message(self):
        msg = build_reminder(3)
        assert "📦" in msg
        assert "3 筆待出貨" in msg

    def test_high_count_urgent_message(self):
        msg = build_reminder(8)
        assert "⚡" in msg
        assert "趕快處理" in msg

    def test_sign_off(self):
        msg = build_reminder(2)
        assert "OMG Coffee" in msg

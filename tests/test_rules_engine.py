"""Tests for the rules engine."""
import json
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from biz.income.platforms.base import DailySummary
from biz.income.rules_engine import evaluate, Flag, RulesResult, save_review_queue, load_review_queue


def _summary(platform="iChef", revenue=8000, orders=30, error=None, pending=None):
    return DailySummary(
        platform=platform,
        revenue=revenue,
        orders=orders,
        error=error,
        pending_actions=pending or [],
    )


def _totals(revenue=15000, orders=60):
    return {"revenue": revenue, "orders": orders, "by_platform": {}}


class TestExclusionRules:
    """CLAUDE.md Section 2b: 7 exclusion rules."""

    def test_EX1_negative_revenue_flagged(self):
        summaries = [_summary(revenue=-500)]
        result = evaluate(summaries, _totals())
        reds = result.red_flags()
        assert any(f.rule_id == "EX1" for f in reds)

    def test_EX3_api_error_flagged(self):
        summaries = [_summary(error="Connection timeout")]
        result = evaluate(summaries, _totals())
        reds = result.red_flags()
        assert any(f.rule_id == "EX3" for f in reds)

    def test_EX7_bulk_keyword_in_pending(self):
        summaries = [_summary(platform="Shopee", pending=["批量訂單 waiting"])]
        result = evaluate(summaries, _totals())
        yellows = result.yellow_flags()
        assert any(f.rule_id == "EX7" for f in yellows)

    def test_clean_platform_auto_ok(self):
        summaries = [_summary(revenue=5000, orders=20)]
        result = evaluate(summaries, _totals())
        assert "iChef" in result.auto_ok


class TestAlerts:
    @patch("biz.income.rules_engine.datetime")
    @patch("biz.income.rules_engine.storage")
    def test_slow_day_alert(self, mock_storage, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 25, 16, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        mock_storage.get_pending_actions.return_value = []
        mock_storage.get_totals.return_value = {"revenue": 0, "orders": 0, "by_platform": {}}
        summaries = [_summary(revenue=1000, orders=5)]
        result = evaluate(summaries, _totals(revenue=2000))
        alert_ids = [a.rule_id for a in result.alerts]
        assert "AL1" in alert_ids

    @patch("biz.income.rules_engine.storage")
    def test_great_day_celebration(self, mock_storage):
        mock_storage.get_pending_actions.return_value = []
        mock_storage.get_totals.return_value = {"revenue": 0, "orders": 0, "by_platform": {}}
        summaries = [_summary(revenue=25000, orders=100)]
        result = evaluate(summaries, _totals(revenue=25000))
        celebrations = result.celebrations()
        assert len(celebrations) > 0

    def test_has_critical_set_on_red_flags(self):
        summaries = [_summary(revenue=-100)]
        result = evaluate(summaries, _totals())
        assert result.has_critical


class TestRulesResult:
    def test_red_flags_filter(self):
        r = RulesResult(flags=[
            Flag("EX1", "iChef", "red", "test"),
            Flag("EX2", "Shopee", "yellow", "test"),
        ])
        assert len(r.red_flags()) == 1
        assert len(r.yellow_flags()) == 1

    def test_empty_result(self):
        r = RulesResult()
        assert r.red_flags() == []
        assert r.yellow_flags() == []
        assert r.celebrations() == []
        assert not r.has_critical


class TestReviewQueue:
    def test_save_and_load(self, tmp_path):
        queue_path = tmp_path / "review_queue.json"
        with patch("biz.income.rules_engine.REVIEW_QUEUE_PATH", queue_path):
            flags = [Flag("EX1", "iChef", "red", "Test flag")]
            save_review_queue(flags)

            loaded = load_review_queue()
            assert len(loaded) == 1
            assert loaded[0]["rule_id"] == "EX1"
            assert loaded[0]["resolved"] is False

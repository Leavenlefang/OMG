"""Tests for the menu engine."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from biz.menu.engine import (
    load_menu, get_platform_menu, check_price_changes,
    find_new_items, MenuItem, summary, MENU_PATH,
)


class TestLoadMenu:
    def test_loads_all_items(self):
        items = load_menu()
        assert len(items) > 0

    def test_no_duplicate_ids(self):
        items = load_menu()
        ids = [i.id for i in items]
        assert len(ids) == len(set(ids))

    def test_all_items_have_required_fields(self):
        items = load_menu()
        for item in items:
            assert item.id
            assert item.name_zh
            assert item.name_en
            assert item.category
            assert item.base_price > 0


class TestPlatformMenu:
    def test_ichef_has_drinks(self):
        items = get_platform_menu("iChef")
        categories = {i.category for i in items}
        assert "drink" in categories

    def test_easystore_has_subscriptions(self):
        items = get_platform_menu("EasyStore")
        categories = {i.category for i in items}
        assert "subscription" in categories

    def test_shopee_no_dine_in_only(self):
        """Shopee shouldn't have items only for dine-in (like cappuccino)."""
        items = get_platform_menu("Shopee")
        ids = {i.id for i in items}
        assert "omg-cappuccino" not in ids  # only on iChef + Uber Eats

    def test_invalid_platform_raises(self):
        with pytest.raises(Exception):
            get_platform_menu("FakePlatform")


class TestAvailability:
    def test_in_stock_item_is_available(self):
        items = load_menu()
        latte = next(i for i in items if i.id == "omg-latte")
        assert latte.is_available()

    def test_seasonal_item_within_window(self):
        items = load_menu()
        sakura = next(i for i in items if i.id == "sakura-latte")
        assert sakura.is_available(on_date=date(2026, 3, 25))

    def test_seasonal_item_outside_window(self):
        items = load_menu()
        sakura = next(i for i in items if i.id == "sakura-latte")
        assert not sakura.is_available(on_date=date(2026, 6, 1))

    def test_out_of_stock_not_available(self):
        item = MenuItem({
            "id": "test", "name_zh": "測試", "name_en": "Test",
            "category": "drink", "base_price": 100, "in_stock": False,
        })
        assert not item.is_available()


class TestPriceChangeDetection:
    def test_detects_large_price_change(self):
        old = [MenuItem({"id": "x", "name_zh": "X", "name_en": "X", "category": "drink", "base_price": 100})]
        new = [MenuItem({"id": "x", "name_zh": "X", "name_en": "X", "category": "drink", "base_price": 130})]
        flags = check_price_changes(old, new)
        assert len(flags) == 1
        assert flags[0]["change_pct"] == 30.0

    def test_ignores_small_price_change(self):
        old = [MenuItem({"id": "x", "name_zh": "X", "name_en": "X", "category": "drink", "base_price": 100})]
        new = [MenuItem({"id": "x", "name_zh": "X", "name_en": "X", "category": "drink", "base_price": 110})]
        flags = check_price_changes(old, new)
        assert len(flags) == 0

    def test_finds_new_items(self):
        old = [MenuItem({"id": "a", "name_zh": "A", "name_en": "A", "category": "drink", "base_price": 100})]
        new = [
            MenuItem({"id": "a", "name_zh": "A", "name_en": "A", "category": "drink", "base_price": 100}),
            MenuItem({"id": "b", "name_zh": "B", "name_en": "B", "category": "drink", "base_price": 150}),
        ]
        new_items = find_new_items(old, new)
        assert len(new_items) == 1
        assert new_items[0].id == "b"


class TestSummary:
    def test_summary_returns_string(self):
        s = summary()
        assert "Menu:" in s
        assert "items available" in s

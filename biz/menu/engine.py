"""
Menu engine — single source of truth for all platform menus.

Reads menu.yaml → validates → generates per-platform menus.
Enforces CLAUDE.md Section 4 rules:
  - in_stock=false disables on all platforms
  - seasonal items filtered by available_from / available_until
  - price changes > 20% flagged for human review
  - New items (no prior version) flagged for review before publish
"""

from datetime import date
from pathlib import Path
from typing import Optional

import yaml

MENU_PATH = Path(__file__).parent / "menu.yaml"
VALID_PLATFORMS = {"iChef", "Uber Eats", "Shopee", "EasyStore"}


class MenuError(Exception):
    pass


class MenuItem:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name_zh = data["name_zh"]
        self.name_en = data["name_en"]
        self.category = data["category"]
        self.base_price = data["base_price"]
        self.in_stock = data.get("in_stock", True)
        self.platforms = data.get("platforms", [])
        self.options = data.get("options", [])
        self.tags = data.get("tags", [])
        self.available_from = data.get("available_from")
        self.available_until = data.get("available_until")
        self._raw = data

    def is_available(self, on_date: Optional[date] = None) -> bool:
        """Check if item is in stock and within seasonal window."""
        if not self.in_stock:
            return False
        d = on_date or date.today()
        if self.available_from and d < date.fromisoformat(str(self.available_from)):
            return False
        if self.available_until and d > date.fromisoformat(str(self.available_until)):
            return False
        return True

    def for_platform(self, platform: str) -> bool:
        """Check if item should appear on a given platform."""
        return platform in self.platforms and self.is_available()

    def to_dict(self) -> dict:
        return self._raw.copy()


def load_menu() -> list[MenuItem]:
    """Load and validate the master menu."""
    if not MENU_PATH.exists():
        raise MenuError(f"Menu file not found: {MENU_PATH}")

    with open(MENU_PATH) as f:
        data = yaml.safe_load(f)

    if not data or "items" not in data:
        raise MenuError("Menu file is empty or missing 'items' key")

    items = []
    seen_ids = set()
    for entry in data["items"]:
        # Validate required fields
        for field in ("id", "name_zh", "name_en", "category", "base_price"):
            if field not in entry:
                raise MenuError(f"Item missing required field '{field}': {entry}")

        if entry["id"] in seen_ids:
            raise MenuError(f"Duplicate item ID: {entry['id']}")
        seen_ids.add(entry["id"])

        # Validate platforms
        for p in entry.get("platforms", []):
            if p not in VALID_PLATFORMS:
                raise MenuError(f"Unknown platform '{p}' in item {entry['id']}")

        items.append(MenuItem(entry))

    return items


def get_platform_menu(platform: str, on_date: Optional[date] = None) -> list[MenuItem]:
    """Get all available items for a specific platform."""
    if platform not in VALID_PLATFORMS:
        raise MenuError(f"Unknown platform: {platform}")

    items = load_menu()
    return [item for item in items if item.for_platform(platform)]


def check_price_changes(old_menu: list[MenuItem], new_menu: list[MenuItem]) -> list[dict]:
    """Compare two menu versions, flag price changes > 20% for human review."""
    old_prices = {item.id: item.base_price for item in old_menu}
    flags = []

    for item in new_menu:
        if item.id in old_prices:
            old_price = old_prices[item.id]
            if old_price == 0:
                continue
            change_pct = abs(item.base_price - old_price) / old_price * 100
            if change_pct > 20:
                flags.append({
                    "item_id": item.id,
                    "name": item.name_zh,
                    "old_price": old_price,
                    "new_price": item.base_price,
                    "change_pct": change_pct,
                    "message": f"⚠️ {item.name_zh} 價格變動 {change_pct:.0f}% "
                               f"(NT${old_price} → NT${item.base_price})，需人工確認",
                })

    return flags


def find_new_items(old_menu: list[MenuItem], new_menu: list[MenuItem]) -> list[MenuItem]:
    """Find items in new menu that don't exist in old menu (need photo review)."""
    old_ids = {item.id for item in old_menu}
    return [item for item in new_menu if item.id not in old_ids]


def set_stock(item_id: str, in_stock: bool) -> None:
    """Toggle in_stock for an item. Immediately affects all platforms."""
    with open(MENU_PATH) as f:
        data = yaml.safe_load(f)

    found = False
    for item in data["items"]:
        if item["id"] == item_id:
            item["in_stock"] = in_stock
            found = True
            break

    if not found:
        raise MenuError(f"Item not found: {item_id}")

    with open(MENU_PATH, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def summary() -> str:
    """Quick text summary of current menu status."""
    items = load_menu()
    total = len(items)
    available = sum(1 for i in items if i.is_available())
    out_of_stock = sum(1 for i in items if not i.in_stock)
    seasonal = sum(1 for i in items if i.available_from or i.available_until)

    by_platform = {}
    for p in VALID_PLATFORMS:
        by_platform[p] = sum(1 for i in items if i.for_platform(p))

    lines = [
        f"📋 Menu: {available}/{total} items available",
        f"   Out of stock: {out_of_stock} | Seasonal: {seasonal}",
    ]
    for p in sorted(by_platform):
        lines.append(f"   {p}: {by_platform[p]} items")

    return "\n".join(lines)

"""
Income aggregator — fetches today's data from all platforms and stores it.
"""

from pathlib import Path
from typing import Optional

import yaml

from .platforms.base import DailySummary
from .platforms.ichef import IChefPlatform
from .platforms.ubereats import UberEatsPlatform
from .platforms.shopee import ShopeePlatform
from .platforms.easystore import EasyStorePlatform
from . import storage

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def build_platforms(config: dict):
    cfg = config.get("platforms", {})
    return [
        IChefPlatform(cfg.get("ichef", {})),
        UberEatsPlatform(cfg.get("ubereats", {})),
        ShopeePlatform(cfg.get("shopee", {})),
        EasyStorePlatform(cfg.get("easystore", {})),
    ]


def run() -> list[DailySummary]:
    """Fetch all platforms and persist results. Returns list of summaries."""
    config = load_config()
    storage.init_db()

    platforms = build_platforms(config)
    summaries = []

    for platform in platforms:
        print(f"  → Fetching {platform.name}...", end=" ", flush=True)
        summary = platform.fetch_today()
        storage.upsert(summary)
        summaries.append(summary)

        if summary.error:
            print(f"ERROR: {summary.error}")
        elif summary.is_mock:
            print(f"NT${summary.revenue:,.0f} / {summary.orders} orders  [MOCK]")
        else:
            print(f"NT${summary.revenue:,.0f} / {summary.orders} orders")

    return summaries

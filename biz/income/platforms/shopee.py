"""
Shopee platform adapter.

Real API docs: https://open.shopee.com/documents
Required config:
  shopee:
    partner_id: 12345
    shop_id: 67890
    partner_key: "abc..."
    # OR set mock: true to use mock data
    mock: true
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta

from .base import Platform, DailySummary


class ShopeePlatform(Platform):
    name = "Shopee"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.mock = self.cfg.get("mock", True)

    def fetch_today(self) -> DailySummary:
        if self.mock:
            return self._mock_summary(
                revenue=1850,
                orders=8,
                top_items=[
                    {"name": "精品掛耳包 x10", "qty": 3},
                    {"name": "咖啡豆 200g", "qty": 2},
                ],
                pending=[
                    "3 orders ready to ship",
                    "1 customer message unread",
                ],
            )

        try:
            return self._fetch_real()
        except Exception as e:
            return self._error_summary(f"Shopee API error: {e}")

    def _fetch_real(self) -> DailySummary:
        # ── Real Shopee Open Platform integration ──
        # Uncomment and fill in once you have credentials in config.yaml
        #
        # import requests
        # partner_id = int(self.cfg["partner_id"])
        # shop_id    = int(self.cfg["shop_id"])
        # key        = self.cfg["partner_key"]
        #
        # now = int(time.time())
        # path = "/api/v2/order/get_order_list"
        # base_str = f"{partner_id}{path}{now}"
        # sign = hmac.new(key.encode(), base_str.encode(), hashlib.sha256).hexdigest()
        #
        # today_start = int(datetime.now().replace(hour=0,minute=0,second=0).timestamp())
        # params = {
        #     "partner_id": partner_id,
        #     "shop_id": shop_id,
        #     "timestamp": now,
        #     "sign": sign,
        #     "time_range_field": "create_time",
        #     "time_from": today_start,
        #     "time_to": now,
        #     "page_size": 100,
        #     "order_status": "READY_TO_SHIP,SHIPPED,COMPLETED",
        # }
        # r = requests.get("https://partner.shopeemobile.com" + path, params=params)
        # r.raise_for_status()
        # data = r.json()
        # orders = data["response"]["order_list"]
        # revenue = sum(float(o.get("total_amount", 0)) for o in orders)
        # return DailySummary(platform=self.name, revenue=revenue, orders=len(orders))

        raise NotImplementedError("Add Shopee credentials to config.yaml and uncomment _fetch_real()")

"""
EasyStore platform adapter.

Real API docs: https://developer.easystore.co/
Required config:
  easystore:
    access_token: "..."
    store_id: "..."
    mock: true
"""

from datetime import datetime, timezone

from .base import Platform, DailySummary


class EasyStorePlatform(Platform):
    name = "EasyStore"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.mock = self.cfg.get("mock", True)

    def fetch_today(self) -> DailySummary:
        if self.mock:
            return self._mock_summary(
                revenue=1200,
                orders=4,
                top_items=[
                    {"name": "濾掛咖啡禮盒", "qty": 2},
                    {"name": "咖啡豆訂閱方案", "qty": 1},
                ],
                pending=[
                    "1 order awaiting payment",
                ],
            )

        try:
            return self._fetch_real()
        except Exception as e:
            return self._error_summary(f"EasyStore API error: {e}")

    def _fetch_real(self) -> DailySummary:
        # ── Real EasyStore REST API integration ──
        # Uncomment once you have credentials in config.yaml
        #
        # import requests
        # token    = self.cfg["access_token"]
        # store_id = self.cfg["store_id"]
        # headers  = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        #
        # today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # r = requests.get(
        #     f"https://api.easystore.co/v1/{store_id}/orders",
        #     headers=headers,
        #     params={"created_at_min": today, "status": "paid,shipped,completed", "limit": 250},
        # )
        # r.raise_for_status()
        # orders = r.json().get("orders", [])
        # revenue = sum(float(o.get("total_price", 0)) for o in orders)
        # return DailySummary(platform=self.name, revenue=revenue, orders=len(orders))

        raise NotImplementedError("Add EasyStore credentials to config.yaml and uncomment _fetch_real()")

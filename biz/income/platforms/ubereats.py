"""
Uber Eats platform adapter.

Real API docs: https://developer.uber.com/docs/eats/introduction
Required config:
  ubereats:
    client_id: "..."
    client_secret: "..."
    store_id: "..."
    mock: true
"""

from .base import Platform, DailySummary


class UberEatsPlatform(Platform):
    name = "Uber Eats"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.mock = self.cfg.get("mock", True)

    def fetch_today(self) -> DailySummary:
        if self.mock:
            return self._mock_summary(
                revenue=3200,
                orders=14,
                top_items=[
                    {"name": "拿鐵", "qty": 6},
                    {"name": "美式咖啡", "qty": 4},
                    {"name": "卡布奇諾", "qty": 3},
                ],
                pending=[
                    "2 orders in preparation",
                ],
            )

        try:
            return self._fetch_real()
        except Exception as e:
            return self._error_summary(f"Uber Eats API error: {e}")

    def _fetch_real(self) -> DailySummary:
        # ── Real Uber Eats Order API integration ──
        # Uncomment once you have credentials in config.yaml
        #
        # import requests
        # from datetime import datetime, timezone
        #
        # # 1. Get OAuth token
        # r = requests.post("https://login.uber.com/oauth/v2/token", data={
        #     "client_id":     self.cfg["client_id"],
        #     "client_secret": self.cfg["client_secret"],
        #     "grant_type":    "client_credentials",
        #     "scope":         "eats.order",
        # })
        # token = r.json()["access_token"]
        # headers = {"Authorization": f"Bearer {token}"}
        #
        # # 2. Fetch today's orders
        # today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
        # store_id = self.cfg["store_id"]
        # r = requests.get(
        #     f"https://api.uber.com/v1/eats/stores/{store_id}/orders",
        #     headers=headers,
        #     params={"start_time": today, "status": "completed,active"},
        # )
        # orders = r.json().get("orders", [])
        # revenue = sum(float(o.get("price", {}).get("total_price", 0)) / 100 for o in orders)
        # return DailySummary(platform=self.name, revenue=revenue, orders=len(orders))

        raise NotImplementedError("Add Uber Eats credentials to config.yaml and uncomment _fetch_real()")

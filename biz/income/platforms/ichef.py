"""
iChef platform adapter.

iChef does not have a public REST API.
Options (in order of effort):
  A. Export daily reports from iChef dashboard → parse CSV  (easiest)
  B. Screen-scrape iChef web dashboard via requests + BeautifulSoup
  C. Use iChef's unofficial internal API (inspect browser network tab)

Set mock: true until you choose an approach.

config:
  ichef:
    mock: true
    # Option A — CSV export path (iChef can email you a daily CSV):
    # csv_dir: "/Users/you/Downloads/ichef_reports"
    # Option B/C — web credentials:
    # username: "..."
    # password: "..."
"""

import csv
import glob
import os
from datetime import datetime

from .base import Platform, DailySummary


class IChefPlatform(Platform):
    name = "iChef"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.mock = self.cfg.get("mock", True)

    def fetch_today(self) -> DailySummary:
        if self.mock:
            return self._mock_summary(
                revenue=8400,
                orders=37,
                top_items=[
                    {"name": "手沖咖啡", "qty": 12},
                    {"name": "拿鐵", "qty": 10},
                    {"name": "蛋糕套餐", "qty": 7},
                ],
                pending=[],
            )

        csv_dir = self.cfg.get("csv_dir")
        if csv_dir:
            return self._fetch_from_csv(csv_dir)

        return self._error_summary(
            "iChef: set mock:true or configure csv_dir in config.yaml"
        )

    def _fetch_from_csv(self, csv_dir: str) -> DailySummary:
        today = datetime.now().strftime("%Y-%m-%d")
        pattern = os.path.join(csv_dir, f"*{today}*.csv")
        files = sorted(glob.glob(pattern))
        if not files:
            return self._error_summary(f"iChef: no CSV found for {today} in {csv_dir}")

        revenue = 0.0
        orders = 0
        try:
            with open(files[-1], encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Adjust column names to match your iChef export format
                    revenue += float(row.get("金額", row.get("total", 0)))
                    orders += 1
        except Exception as e:
            return self._error_summary(f"iChef CSV parse error: {e}")

        return DailySummary(platform=self.name, revenue=revenue, orders=orders)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DailySummary:
    platform: str
    revenue: float           # in TWD
    orders: int
    currency: str = "TWD"
    top_items: list = field(default_factory=list)   # [{"name": str, "qty": int}]
    pending_actions: list = field(default_factory=list)  # ["2 orders to ship"]
    alerts: list = field(default_factory=list)       # ["No orders in last 2h"]
    fetched_at: datetime = field(default_factory=datetime.now)
    is_mock: bool = False
    error: Optional[str] = None


class Platform:
    name: str = "unknown"
    currency: str = "TWD"

    def fetch_today(self) -> DailySummary:
        raise NotImplementedError

    def _mock_summary(self, revenue: float, orders: int, top_items: list = None, pending: list = None) -> DailySummary:
        return DailySummary(
            platform=self.name,
            revenue=revenue,
            orders=orders,
            top_items=top_items or [],
            pending_actions=pending or [],
            is_mock=True,
        )

    def _error_summary(self, error: str) -> DailySummary:
        return DailySummary(
            platform=self.name,
            revenue=0,
            orders=0,
            error=error,
        )

"""
WooCommerce REST API client.
Fetches new orders, updates order status, processes refunds.
Falls back to mock data when DEMO_MODE=true or WC_URL not set.
"""
import logging
import httpx

logger = logging.getLogger(__name__)


class WooCommerceClient:
    def __init__(self, url, consumer_key, consumer_secret):
        self.base = url.rstrip("/") + "/wp-json/wc/v3"
        self.auth = (consumer_key, consumer_secret)

    def get_orders(self, status="processing", per_page=20):
        """Fetch orders pending fulfillment."""
        try:
            resp = httpx.get(
                f"{self.base}/orders",
                auth=self.auth,
                params={"status": status, "per_page": per_page},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("WC get_orders failed: %s", exc)
            return []

    def update_order_status(self, order_id, status, tracking=None):
        """Update order status in WooCommerce."""
        payload = {"status": status}
        if tracking:
            payload["meta_data"] = [{"key": "tracking_number", "value": tracking}]
        try:
            resp = httpx.put(
                f"{self.base}/orders/{order_id}",
                auth=self.auth,
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("WC update_order failed for %s: %s", order_id, exc)
            return False

    def create_refund(self, order_id, amount=None, reason="Customer request"):
        """Issue a full or partial refund."""
        payload = {"reason": reason}
        if amount:
            payload["amount"] = str(amount)
        try:
            resp = httpx.post(
                f"{self.base}/orders/{order_id}/refunds",
                auth=self.auth,
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("WC refund failed for %s: %s", order_id, exc)
            return False


class MockWooCommerceClient(WooCommerceClient):
    """Mock client for demo mode. Generates fake orders for testing."""

    def __init__(self):
        pass

    def get_orders(self, status="processing", per_page=20):
        import random
        from datetime import datetime, timezone
        orders = []
        for i in range(random.randint(0, 3)):
            orders.append({
                "id": random.randint(1000, 9999),
                "status": "processing",
                "total": str(round(random.uniform(19.99, 89.99), 2)),
                "date_created": datetime.now(timezone.utc).isoformat(),
                "billing": {
                    "first_name": "Test",
                    "last_name": "Customer",
                    "email": f"test{i}@example.com",
                },
                "line_items": [
                    {
                        "product_id": random.randint(1, 10),
                        "quantity": 1,
                        "price": str(round(random.uniform(19.99, 89.99), 2)),
                    }
                ],
            })
        return orders

    def update_order_status(self, order_id, status, tracking=None):
        logger.info("[MOCK WC] Order %s → %s (tracking: %s)", order_id, status, tracking)
        return True

    def create_refund(self, order_id, amount=None, reason=""):
        logger.info("[MOCK WC] Refund for order %s: $%s", order_id, amount)
        return True


def get_client(app=None):
    if app:
        config = app.config
    else:
        from flask import current_app
        config = current_app.config

    demo = config.get("DEMO_MODE", True)
    url = config.get("WC_URL", "")
    if demo or not url:
        return MockWooCommerceClient()
    return WooCommerceClient(url, config.get("WC_KEY", ""), config.get("WC_SECRET", ""))

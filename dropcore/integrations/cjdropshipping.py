"""
CJDropshipping API client (free tier).
Docs: https://developers.cjdropshipping.com/
Covers: product search, stock check, order placement, tracking.
"""
import logging
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"


class CJClient:
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password
        self._token = None

    def _auth(self):
        """Obtain access token. CJ uses email+password auth."""
        if self._token:
            return self._token
        if not self.email or not self.password:
            logger.warning("CJ credentials not set — running in mock mode")
            return None
        try:
            resp = httpx.post(
                f"{BASE_URL}/authentication/getAccessToken",
                json={"email": self.email, "password": self.password},
                timeout=10,
            )
            data = resp.json()
            if data.get("result"):
                self._token = data["data"]["accessToken"]
                return self._token
        except Exception as exc:
            logger.warning("CJ auth failed: %s", exc)
        return None

    def _headers(self):
        token = self._auth()
        if not token:
            return {}
        return {"CJ-Access-Token": token}

    def search_products(self, keyword, page=1, page_size=20):
        """Search CJ product catalog."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/product/list",
                headers=self._headers(),
                params={
                    "productNameEn": keyword,
                    "pageNum": page,
                    "pageSize": page_size,
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("result"):
                return data.get("data", {}).get("list", [])
        except Exception as exc:
            logger.warning("CJ product search failed: %s", exc)
        return []

    def get_stock(self, product_id):
        """Check stock level for a CJ product."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/product/stock/queryByVid",
                headers=self._headers(),
                params={"vid": product_id},
                timeout=10,
            )
            data = resp.json()
            if data.get("result"):
                return data.get("data", {}).get("quantity", 0)
        except Exception as exc:
            logger.warning("CJ stock check failed for %s: %s", product_id, exc)
        return -1  # -1 = unknown

    def place_order(self, order_payload):
        """
        Place a dropship order with CJ.
        order_payload: dict matching CJ's createOrder schema.
        """
        try:
            resp = httpx.post(
                f"{BASE_URL}/shopping/order/createOrder",
                headers=self._headers(),
                json=order_payload,
                timeout=15,
            )
            data = resp.json()
            if data.get("result"):
                return data.get("data", {})
            logger.warning("CJ order placement failed: %s", data.get("message"))
        except Exception as exc:
            logger.warning("CJ order placement exception: %s", exc)
        return None

    def get_tracking(self, order_id):
        """Fetch tracking number for a CJ order."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/logistic/trackInfo",
                headers=self._headers(),
                params={"orderId": order_id},
                timeout=10,
            )
            data = resp.json()
            if data.get("result"):
                tracks = data.get("data", {}).get("tracks", [])
                if tracks:
                    return tracks[0].get("trackingNumber")
        except Exception as exc:
            logger.warning("CJ tracking fetch failed: %s", exc)
        return None


# ------------------------------------------------------------------
# Mock implementations for demo/testing (DEMO_MODE=true)
# ------------------------------------------------------------------

MOCK_PRODUCTS = [
    {
        "pid": "mock-001",
        "productNameEn": "LED Magnetic Phone Mount",
        "sellPrice": 4.50,
        "quantity": 250,
        "categoryName": "Phone Accessories",
    },
    {
        "pid": "mock-002",
        "productNameEn": "Silicone Cable Organizer Set",
        "sellPrice": 2.80,
        "quantity": 890,
        "categoryName": "Home Gadgets",
    },
    {
        "pid": "mock-003",
        "productNameEn": "Posture Corrector Back Brace",
        "sellPrice": 7.20,
        "quantity": 320,
        "categoryName": "Health & Fitness",
    },
]


class MockCJClient(CJClient):
    """Returns mock data — used when DEMO_MODE=true or no credentials."""

    def search_products(self, keyword, page=1, page_size=20):
        return [p for p in MOCK_PRODUCTS if keyword.lower() in p["productNameEn"].lower()] or MOCK_PRODUCTS

    def get_stock(self, product_id):
        return {"mock-001": 250, "mock-002": 890, "mock-003": 320}.get(product_id, 50)

    def place_order(self, order_payload):
        return {"orderId": "MOCK-ORD-12345", "trackingNumber": "MOCK-TRACK-99"}

    def get_tracking(self, order_id):
        return "MOCK-TRACK-99"


def get_client(app):
    from ..config import Config
    if Config.DEMO_MODE or not Config.CJ_EMAIL:
        return MockCJClient()
    return CJClient(email=Config.CJ_EMAIL, password=Config.CJ_PASSWORD)

"""
AliExpress product scraper.
Scrapes bestsellers to find products with 500-5000 orders
(validated demand, not yet saturated).
"""
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_URL = "https://www.aliexpress.com/wholesale"


def search_products(keyword, min_orders=500, max_orders=5000, max_results=20):
    """
    Search AliExpress for products matching keyword.
    Returns list of product dicts filtered by order count range.
    Industry secret: 500-5000 orders = validated demand without full saturation.
    """
    products = []
    try:
        params = {
            "SearchText": keyword,
            "SortType": "total_tranpro_desc",  # sort by orders
            "page": 1,
        }
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(SEARCH_URL, params=params)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            items = soup.select("[class*='product-snippet']") or soup.select("[class*='item']")
            for item in items[:max_results]:
                product = _parse_item(item)
                if product and min_orders <= product.get("orders", 0) <= max_orders:
                    products.append(product)

    except Exception as exc:
        logger.warning("AliExpress scrape failed for '%s': %s", keyword, exc)

    return products


def _parse_item(item):
    """Extract product details from a BeautifulSoup element."""
    try:
        title_el = item.select_one("[class*='title']") or item.select_one("h3")
        price_el = item.select_one("[class*='price']")
        orders_el = item.select_one("[class*='trade']") or item.select_one("[class*='order']")
        link_el = item.select_one("a[href]")
        img_el = item.select_one("img")

        title = title_el.get_text(strip=True) if title_el else "Unknown"
        price_text = price_el.get_text(strip=True) if price_el else "0"
        orders_text = orders_el.get_text(strip=True) if orders_el else "0"

        # Parse price — take the first number found
        price_match = re.search(r"[\d.]+", price_text.replace(",", ""))
        price = float(price_match.group()) if price_match else 0.0

        # Parse order count
        orders_match = re.search(r"([\d,]+)", orders_text)
        orders = int(orders_match.group(1).replace(",", "")) if orders_match else 0

        url = link_el["href"] if link_el else ""
        if url and not url.startswith("http"):
            url = "https:" + url

        img = img_el.get("src") or img_el.get("data-src", "") if img_el else ""

        return {
            "title": title,
            "cost_price": price,
            "orders": orders,
            "url": url,
            "image_url": img,
        }
    except Exception:
        return None


def estimate_sell_price(cost_price, target_margin=0.45):
    """
    Calculate recommended sell price for target margin.
    Industry standard: 40-50% margin minimum.
    """
    if cost_price <= 0:
        return 0.0
    return round(cost_price / (1 - target_margin), 2)

"""
Margin calculation helpers.
Industry standard: 40-50% gross margin minimum for sustainable dropshipping.
"""


def gross_margin(sell_price, cost_price):
    """Return gross margin percentage."""
    if not sell_price or sell_price <= 0:
        return 0.0
    return round((sell_price - cost_price) / sell_price * 100, 2)


def net_margin(sell_price, cost_price, shipping_cost=0, platform_fee_pct=0.03, ad_spend=0):
    """
    Return net margin after all costs.
    platform_fee_pct: WooCommerce payment gateway ~3%
    """
    if not sell_price or sell_price <= 0:
        return 0.0
    platform_fee = sell_price * platform_fee_pct
    net_profit = sell_price - cost_price - shipping_cost - platform_fee - ad_spend
    return round(net_profit / sell_price * 100, 2)


def recommended_sell_price(cost_price, target_margin=0.45):
    """Calculate sell price to hit target margin."""
    if cost_price <= 0:
        return 0.0
    return round(cost_price / (1 - target_margin), 2)


def roas(revenue, ad_spend):
    """Return on ad spend ratio."""
    if not ad_spend or ad_spend <= 0:
        return 0.0
    return round(revenue / ad_spend, 2)


def cac(ad_spend, new_customers):
    """Customer acquisition cost."""
    if not new_customers or new_customers <= 0:
        return 0.0
    return round(ad_spend / new_customers, 2)

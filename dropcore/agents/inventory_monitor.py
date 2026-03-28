"""
InventoryMonitorAgent — every 2 hours.
Industry secret: auto-hide products when supplier stock < 5 units.
Prevents overselling disasters that cause refunds and chargebacks.
Kill slow-movers in 14 days — fail fast, scale winners.
"""
import logging
from datetime import datetime, timezone, timedelta
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

STOCK_HIDE_THRESHOLD = 5       # hide product below this supplier stock
STOCK_ALERT_THRESHOLD = 20     # alert when bestseller stock drops here
SLOW_MOVER_DAYS = 14           # flag products with 0 orders in this period


class InventoryMonitorAgent(BaseAgent):
    name = "InventoryMonitorAgent"

    def execute(self) -> str:
        from ..database import db
        from ..models.product import Product
        from ..models.order import OrderItem
        from ..integrations.cjdropshipping import get_client
        from ..utils.notifications import notify

        cj = get_client(self.app)
        products = Product.query.filter(Product.status.in_(["active", "testing"])).all()

        hidden = 0
        alerted = 0
        slow_movers = 0

        for product in products:
            if not product.sku:
                continue

            stock = cj.get_stock(product.sku)
            if stock == -1:
                continue  # unknown — skip

            product.supplier_stock = stock

            # Auto-hide if stock critically low
            if stock < STOCK_HIDE_THRESHOLD and product.status == "active":
                product.status = "unlisted"
                hidden += 1
                notify(f"[STOCK] '{product.title[:40]}' hidden — only {stock} units left")
                logger.warning("Hidden '%s' — stock: %d", product.title, stock)

            # Alert if bestseller running low
            elif STOCK_HIDE_THRESHOLD <= stock < STOCK_ALERT_THRESHOLD:
                alerted += 1
                notify(f"[STOCK ALERT] '{product.title[:40]}' running low: {stock} units")

            # Re-activate if stock recovered
            elif stock >= STOCK_HIDE_THRESHOLD and product.status == "unlisted":
                product.status = "active"
                logger.info("Re-activated '%s' — stock: %d", product.title, stock)

        db.session.commit()

        # Detect slow movers (0 orders in 14 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=SLOW_MOVER_DAYS)
        active_products = Product.query.filter_by(status="active").all()
        for product in active_products:
            from ..models.order import Order as OrderModel
            recent_orders = OrderItem.query.filter(
                OrderItem.product_id == product.id,
            ).join(OrderItem.order).filter(
                OrderModel.created_at >= cutoff
            ).count()

            if recent_orders == 0:
                slow_movers += 1
                notify(
                    f"[SLOW MOVER] '{product.title[:40]}' — 0 orders in {SLOW_MOVER_DAYS} days. "
                    f"Consider price test or kill."
                )

        return (
            f"Checked {len(products)} products: "
            f"{hidden} hidden (low stock), {alerted} low-stock alerts, "
            f"{slow_movers} slow movers flagged"
        )

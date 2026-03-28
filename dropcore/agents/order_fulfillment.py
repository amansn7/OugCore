"""
OrderFulfillmentAgent — every 15 minutes.
Industry secret: batch 15-min windows are more efficient than instant per-order API calls.
Proactive tracking email immediately = prevents 70% of WISMO tickets.
"""
import logging
from datetime import datetime, timezone
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OrderFulfillmentAgent(BaseAgent):
    name = "OrderFulfillmentAgent"

    def execute(self) -> str:
        from ..database import db
        from ..models.order import Order, OrderItem
        from ..models.product import Product
        from ..integrations.woocommerce import get_client as wc_client
        from ..integrations.cjdropshipping import get_client as cj_client
        from ..integrations.email_client import send_order_confirmation, send_tracking_notification

        wc = wc_client(self.app)
        cj = cj_client(self.app)

        # Fetch new orders from WooCommerce
        wc_orders = self._retry(lambda: wc.get_orders(status="processing"))
        fulfilled = 0
        failed = 0

        for wc_order in wc_orders:
            store_id = str(wc_order["id"])

            # Skip if already in our DB
            if Order.query.filter_by(store_order_id=store_id).first():
                continue

            # Create order record
            billing = wc_order.get("billing", {})
            order = Order(
                store_order_id=store_id,
                customer_email=billing.get("email", ""),
                customer_name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip(),
                status="pending",
                total_revenue=float(wc_order.get("total", 0)),
            )
            db.session.add(order)
            db.session.flush()

            # Add line items
            total_cost = 0.0
            for item in wc_order.get("line_items", []):
                product = Product.query.get(item.get("product_id"))
                cost = product.cost_price if product else float(item.get("price", 0)) * 0.4
                oi = OrderItem(
                    order_id=order.id,
                    product_id=item.get("product_id"),
                    quantity=item.get("quantity", 1),
                    unit_cost=cost,
                    unit_price=float(item.get("price", 0)),
                )
                db.session.add(oi)
                total_cost += cost * oi.quantity

            order.total_cost = round(total_cost, 2)
            order.profit = round(order.total_revenue - order.total_cost, 2)
            db.session.flush()

            # Send confirmation email immediately
            send_order_confirmation(order, self.app)

            # Place order with CJ Dropshipping
            cj_payload = self._build_cj_payload(wc_order, billing)
            cj_result = self._retry(lambda: cj.place_order(cj_payload), retries=3, backoff=2)

            if cj_result:
                tracking = cj_result.get("trackingNumber")
                order.status = "fulfilled"
                order.fulfilled_at = datetime.now(timezone.utc)
                order.supplier_order_id = cj_result.get("orderId", "")
                if tracking:
                    order.tracking_number = tracking
                    send_tracking_notification(order, self.app)
                wc.update_order_status(store_id, "completed", tracking)
                fulfilled += 1
                logger.info("Fulfilled order %s (CJ: %s)", store_id, cj_result.get("orderId"))
            else:
                order.status = "failed"
                order.notes = "CJ fulfillment failed — manual review needed"
                failed += 1
                logger.warning("Fulfillment failed for order %s", store_id)

            db.session.commit()

        return f"Processed {len(wc_orders)} orders: {fulfilled} fulfilled, {failed} failed"

    def _build_cj_payload(self, wc_order, billing):
        """Build CJ order payload from WooCommerce order data."""
        shipping = wc_order.get("shipping", billing)
        return {
            "orderNumber": str(wc_order["id"]),
            "shippingCountry": shipping.get("country", "US"),
            "shippingAddress": shipping.get("address_1", ""),
            "shippingCity": shipping.get("city", ""),
            "shippingZip": shipping.get("postcode", ""),
            "shippingCustomerName": f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip(),
            "shippingPhone": billing.get("phone", ""),
            "products": [
                {
                    "vid": item.get("sku", item.get("product_id", "")),
                    "quantity": item.get("quantity", 1),
                }
                for item in wc_order.get("line_items", [])
            ],
        }

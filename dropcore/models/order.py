from datetime import datetime, timezone
from ..database import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    store_order_id = db.Column(db.String(100), unique=True, nullable=False)
    customer_email = db.Column(db.String(255))
    customer_name = db.Column(db.String(255))
    # pending | fulfilled | shipped | delivered | refunded | failed
    status = db.Column(db.String(20), default="pending")
    total_revenue = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)
    tracking_number = db.Column(db.String(200))
    supplier_order_id = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fulfilled_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def fulfillment_hours(self):
        if self.fulfilled_at and self.created_at:
            delta = self.fulfilled_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "store_order_id": self.store_order_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "status": self.status,
            "total_revenue": self.total_revenue,
            "total_cost": self.total_cost,
            "profit": self.profit,
            "tracking_number": self.tracking_number,
            "fulfillment_hours": self.fulfillment_hours(),
            "created_at": self.created_at.isoformat(),
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_cost = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    supplier_order_id = db.Column(db.String(200))

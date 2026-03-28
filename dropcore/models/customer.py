from datetime import datetime, timezone
from ..database import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    # subscribed | unsubscribed
    email_status = db.Column(db.String(20), default="subscribed")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_order_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "total_orders": self.total_orders,
            "total_spent": self.total_spent,
        }

from datetime import datetime, timezone
from ..database import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # aliexpress | cjdropshipping | eprolo | manual
    platform = db.Column(db.String(50), default="cjdropshipping")
    api_product_id = db.Column(db.String(200))
    avg_fulfillment_days = db.Column(db.Float, default=7.0)
    rating = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", backref="supplier", lazy=True)

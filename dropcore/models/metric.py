from datetime import datetime, timezone, date
from ..database import db


class DailyMetric(db.Model):
    __tablename__ = "daily_metrics"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    total_orders = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    margin_pct = db.Column(db.Float, default=0.0)
    aov = db.Column(db.Float, default=0.0)           # avg order value
    cac = db.Column(db.Float, default=0.0)           # customer acquisition cost
    roas = db.Column(db.Float, default=0.0)          # return on ad spend
    conversion_rate = db.Column(db.Float, default=0.0)
    refund_rate = db.Column(db.Float, default=0.0)
    fulfillment_avg_hours = db.Column(db.Float, default=0.0)
    new_customers = db.Column(db.Integer, default=0)
    returning_customers = db.Column(db.Integer, default=0)
    ad_spend = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "total_orders": self.total_orders,
            "total_revenue": self.total_revenue,
            "total_cost": self.total_cost,
            "total_profit": self.total_profit,
            "margin_pct": self.margin_pct,
            "aov": self.aov,
            "roas": self.roas,
            "conversion_rate": self.conversion_rate,
            "refund_rate": self.refund_rate,
            "fulfillment_avg_hours": self.fulfillment_avg_hours,
        }

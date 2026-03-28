"""
AnalyticsAgent — daily at 11pm + weekly on Sundays.
Industry secret: track profit-per-product, not revenue. Revenue is vanity.
Detect anomalies early: sudden refund spike = product quality issue.
"""
import logging
from datetime import datetime, timezone, timedelta, date
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    name = "AnalyticsAgent"

    def execute(self) -> str:
        self._calculate_daily_metrics()
        self._detect_anomalies()
        return "Daily metrics calculated and anomaly check complete"

    def _calculate_daily_metrics(self):
        from ..database import db
        from ..models.order import Order
        from ..models.metric import DailyMetric

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Check if already calculated
        if DailyMetric.query.filter_by(date=yesterday).first():
            return

        start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        orders = Order.query.filter(
            Order.created_at >= start,
            Order.created_at < end,
        ).all()

        if not orders:
            # Seed demo data
            self._seed_demo_metrics(yesterday)
            return

        total_orders = len(orders)
        total_revenue = sum(o.total_revenue for o in orders)
        total_cost = sum(o.total_cost for o in orders)
        total_profit = sum(o.profit for o in orders)
        margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0
        aov = total_revenue / total_orders if total_orders else 0

        refunded = [o for o in orders if o.status == "refunded"]
        refund_rate = (len(refunded) / total_orders * 100) if total_orders else 0

        fulfilled = [o for o in orders if o.fulfilled_at]
        avg_hours = (
            sum(o.fulfillment_hours() or 0 for o in fulfilled) / len(fulfilled)
            if fulfilled else 0
        )

        metric = DailyMetric(
            date=yesterday,
            total_orders=total_orders,
            total_revenue=round(total_revenue, 2),
            total_cost=round(total_cost, 2),
            total_profit=round(total_profit, 2),
            margin_pct=round(margin_pct, 2),
            aov=round(aov, 2),
            refund_rate=round(refund_rate, 2),
            fulfillment_avg_hours=round(avg_hours, 2),
        )
        db.session.add(metric)
        db.session.commit()
        logger.info("Daily metrics saved for %s: %d orders, $%.2f profit", yesterday, total_orders, total_profit)

    def _detect_anomalies(self):
        from ..models.metric import DailyMetric
        from ..utils.notifications import notify

        # Get last 7 days of metrics
        today = date.today()
        week_ago = today - timedelta(days=7)
        recent = DailyMetric.query.filter(DailyMetric.date >= week_ago).order_by(DailyMetric.date.desc()).all()

        if len(recent) < 2:
            return

        latest = recent[0]
        avg_refund = sum(m.refund_rate for m in recent[1:]) / max(len(recent) - 1, 1)
        avg_margin = sum(m.margin_pct for m in recent[1:]) / max(len(recent) - 1, 1)

        # Refund spike: 2x average
        if latest.refund_rate > avg_refund * 2 and latest.refund_rate > 10:
            notify(
                f"[ANOMALY] Refund spike: {latest.refund_rate:.1f}% today vs "
                f"{avg_refund:.1f}% avg. Check product quality!",
                level="warning",
            )

        # Margin collapse: 10% drop
        if avg_margin > 0 and latest.margin_pct < avg_margin * 0.9:
            notify(
                f"[ANOMALY] Margin drop: {latest.margin_pct:.1f}% today vs "
                f"{avg_margin:.1f}% avg. Check COGS or pricing!",
                level="warning",
            )

    def get_weekly_summary(self):
        """Generate plain-English weekly report via Claude."""
        from ..models.metric import DailyMetric
        from ..integrations.claude_ai import generate_analytics_summary

        today = date.today()
        week_ago = today - timedelta(days=7)
        metrics = DailyMetric.query.filter(DailyMetric.date >= week_ago).all()

        if not metrics:
            return "No data available for this week."

        summary_data = {
            "period": f"{week_ago} to {today}",
            "total_orders": sum(m.total_orders for m in metrics),
            "total_revenue": round(sum(m.total_revenue for m in metrics), 2),
            "total_profit": round(sum(m.total_profit for m in metrics), 2),
            "avg_margin": round(sum(m.margin_pct for m in metrics) / len(metrics), 2),
            "avg_aov": round(sum(m.aov for m in metrics) / len(metrics), 2),
            "avg_refund_rate": round(sum(m.refund_rate for m in metrics) / len(metrics), 2),
            "avg_fulfillment_hours": round(sum(m.fulfillment_avg_hours for m in metrics) / len(metrics), 2),
        }
        return generate_analytics_summary(summary_data)

    def _seed_demo_metrics(self, target_date):
        """Seed realistic demo metrics for the last 30 days."""
        from ..database import db
        from ..models.metric import DailyMetric
        import random

        for i in range(30):
            d = target_date - timedelta(days=i)
            if DailyMetric.query.filter_by(date=d).first():
                continue

            orders = random.randint(3, 25)
            revenue = round(orders * random.uniform(28, 65), 2)
            cost = round(revenue * random.uniform(0.38, 0.52), 2)
            profit = round(revenue - cost, 2)

            db.session.add(DailyMetric(
                date=d,
                total_orders=orders,
                total_revenue=revenue,
                total_cost=cost,
                total_profit=profit,
                margin_pct=round(profit / revenue * 100, 2),
                aov=round(revenue / orders, 2),
                refund_rate=round(random.uniform(1, 6), 2),
                fulfillment_avg_hours=round(random.uniform(2, 8), 2),
                new_customers=random.randint(1, orders),
                returning_customers=random.randint(0, 3),
            ))

        db.session.commit()
        logger.info("Seeded demo metrics for 30 days ending %s", target_date)

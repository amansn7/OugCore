"""
Dashboard blueprint — real-time KPI overview with SSE stream.
"""
import json
import time
from datetime import date, timedelta
from flask import Blueprint, render_template, Response, jsonify, current_app

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/")
def index():
    from ..models.metric import DailyMetric
    from ..models.order import Order
    from ..models.product import Product

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Today's live stats
    today_orders = Order.query.filter(
        Order.created_at >= _day_start(today)
    ).all()
    today_revenue = sum(o.total_revenue for o in today_orders)
    today_profit = sum(o.profit for o in today_orders)
    today_margin = (today_profit / today_revenue * 100) if today_revenue else 0

    # 7-day chart data
    metrics_7d = DailyMetric.query.filter(
        DailyMetric.date >= today - timedelta(days=7)
    ).order_by(DailyMetric.date).all()

    chart_labels = [m.date.strftime("%b %d") for m in metrics_7d]
    chart_revenue = [m.total_revenue for m in metrics_7d]
    chart_profit = [m.total_profit for m in metrics_7d]
    chart_orders = [m.total_orders for m in metrics_7d]

    # Order status breakdown
    statuses = ["pending", "fulfilled", "shipped", "delivered", "refunded", "failed"]
    status_counts = {s: Order.query.filter_by(status=s).count() for s in statuses}

    # Active product count
    active_products = Product.query.filter_by(status="active").count()
    testing_products = Product.query.filter_by(status="testing").count()

    # Latest metric for KPIs
    latest_metric = DailyMetric.query.order_by(DailyMetric.date.desc()).first()

    return render_template(
        "dashboard/index.html",
        today_revenue=round(today_revenue, 2),
        today_profit=round(today_profit, 2),
        today_margin=round(today_margin, 2),
        today_order_count=len(today_orders),
        chart_labels=json.dumps(chart_labels),
        chart_revenue=json.dumps(chart_revenue),
        chart_profit=json.dumps(chart_profit),
        chart_orders=json.dumps(chart_orders),
        status_counts=status_counts,
        active_products=active_products,
        testing_products=testing_products,
        latest_metric=latest_metric,
    )


@bp.route("/stream")
def stream():
    """Server-Sent Events endpoint for live order feed."""
    def event_generator():
        from ..models.order import Order
        last_id = Order.query.count()
        while True:
            time.sleep(5)
            current_count = Order.query.count()
            if current_count > last_id:
                new_orders = Order.query.order_by(Order.id.desc()).limit(current_count - last_id).all()
                for order in new_orders:
                    data = json.dumps(order.to_dict())
                    yield f"data: {data}\n\n"
                last_id = current_count
            else:
                yield ": heartbeat\n\n"

    return Response(event_generator(), mimetype="text/event-stream")


@bp.route("/metrics/json")
def metrics_json():
    """JSON endpoint for dashboard chart refreshes."""
    from ..models.metric import DailyMetric
    today = date.today()
    metrics = DailyMetric.query.filter(
        DailyMetric.date >= today - timedelta(days=30)
    ).order_by(DailyMetric.date).all()
    return jsonify([m.to_dict() for m in metrics])


def _day_start(d):
    from datetime import datetime, timezone
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

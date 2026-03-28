"""
REST API blueprint — webhook receiver for store events + external queries.
POST /api/orders/webhook — receive new orders from WooCommerce webhook
GET  /api/health         — health check
GET  /api/stats          — quick stats JSON
"""
from flask import Blueprint, request, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "DropCore"})


@bp.route("/stats")
def stats():
    from ..models.order import Order
    from ..models.product import Product
    from ..models.metric import DailyMetric
    from datetime import date, timedelta

    today = date.today()
    yesterday = today - timedelta(days=1)
    latest = DailyMetric.query.filter_by(date=yesterday).first()

    return jsonify({
        "total_orders": Order.query.count(),
        "active_products": Product.query.filter_by(status="active").count(),
        "yesterday": latest.to_dict() if latest else {},
    })


@bp.route("/orders/webhook", methods=["POST"])
def order_webhook():
    """
    WooCommerce webhook — triggers immediate order fulfillment.
    Set WooCommerce → Settings → Advanced → Webhooks → order.created → this URL.
    """
    from ..agents.order_fulfillment import OrderFulfillmentAgent
    from flask import current_app
    import threading

    app = current_app._get_current_object()
    agent = OrderFulfillmentAgent(app)
    t = threading.Thread(target=agent.run, daemon=True)
    t.start()

    return jsonify({"status": "processing"}), 202


@bp.route("/products", methods=["GET"])
def list_products():
    from ..models.product import Product
    products = Product.query.filter_by(status="active").all()
    return jsonify([p.to_dict() for p in products])


@bp.route("/research/trigger", methods=["POST"])
def trigger_research():
    """Manually kick off product research agent."""
    from ..agents.product_research import ProductResearchAgent
    from flask import current_app
    import threading

    app = current_app._get_current_object()
    agent = ProductResearchAgent(app)
    t = threading.Thread(target=agent.run, daemon=True)
    t.start()
    return jsonify({"status": "started"})

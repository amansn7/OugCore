"""Orders blueprint — order tracking and management."""
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("orders", __name__, url_prefix="/dashboard/orders")


@bp.route("/")
def index():
    from ..models.order import Order

    status_filter = request.args.get("status", "")
    query = Order.query.order_by(Order.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)

    orders = query.limit(100).all()
    return render_template("dashboard/orders.html", orders=orders, status_filter=status_filter)


@bp.route("/json")
def orders_json():
    from ..models.order import Order

    status = request.args.get("status", "")
    limit = int(request.args.get("limit", 50))
    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify([o.to_dict() for o in query.limit(limit).all()])

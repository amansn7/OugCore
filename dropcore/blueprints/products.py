"""Products blueprint — catalog management + research results."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

bp = Blueprint("products", __name__, url_prefix="/dashboard/products")


@bp.route("/")
def index():
    from ..models.product import Product, ProductResearch

    products = Product.query.order_by(Product.created_at.desc()).all()
    research = ProductResearch.query.order_by(
        ProductResearch.recommended.desc(),
        ProductResearch.trend_score.desc()
    ).limit(20).all()

    return render_template("dashboard/products.html", products=products, research=research)


@bp.route("/add", methods=["POST"])
def add():
    from ..database import db
    from ..models.product import Product

    data = request.form
    product = Product(
        title=data.get("title", ""),
        cost_price=float(data.get("cost_price", 0)),
        sell_price=float(data.get("sell_price", 0)),
        category=data.get("category", ""),
        supplier_url=data.get("supplier_url", ""),
        status="testing",
    )
    product.margin_pct = product.margin()
    db.session.add(product)
    db.session.commit()

    # Trigger marketing content generation
    from ..agents.marketing_content import MarketingContentAgent
    from flask import current_app
    agent = MarketingContentAgent(current_app._get_current_object())
    agent.run()

    return redirect(url_for("products.index"))


@bp.route("/<int:product_id>/status", methods=["POST"])
def update_status(product_id):
    from ..database import db
    from ..models.product import Product

    product = Product.query.get_or_404(product_id)
    product.status = request.form.get("status", product.status)
    db.session.commit()
    return redirect(url_for("products.index"))


@bp.route("/research/json")
def research_json():
    from ..models.product import ProductResearch
    items = ProductResearch.query.order_by(
        ProductResearch.recommended.desc(),
        ProductResearch.trend_score.desc()
    ).limit(50).all()
    return jsonify([r.to_dict() for r in items])

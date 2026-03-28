import logging
from flask import Flask
from .config import Config
from .database import init_db
from .utils.notifications import init_notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    # Import all models so SQLAlchemy knows about them before create_all()
    from .models import Product, ProductResearch, Order, OrderItem, Customer, Supplier, DailyMetric, AgentLog  # noqa: F401

    # Init DB (creates all tables)
    init_db(app)

    # Init notifications
    init_notifications(app)

    # Register blueprints
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.products import bp as products_bp
    from .blueprints.orders import bp as orders_bp
    from .blueprints.agents import bp as agents_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(api_bp)

    # Seed demo data and start scheduler on first request
    with app.app_context():
        _seed_demo_data(app)

    from .scheduler import init_scheduler
    init_scheduler(app)

    return app


def _seed_demo_data(app):
    """Seed initial demo data for out-of-box experience."""
    from .models.product import Product, ProductResearch
    from .models.supplier import Supplier
    from .database import db

    if Product.query.count() > 0:
        return  # already seeded

    # Create demo supplier
    supplier = Supplier(
        name="CJDropshipping Demo",
        platform="cjdropshipping",
        avg_fulfillment_days=5.0,
        rating=4.8,
    )
    db.session.add(supplier)
    db.session.flush()

    # Create demo products
    demo_products = [
        {
            "title": "Magnetic LED Phone Car Mount",
            "cost_price": 4.50, "sell_price": 24.99,
            "category": "Phone Accessories", "status": "active",
            "supplier_stock": 145, "sku": "mock-001",
            "image_url": "https://via.placeholder.com/200x200?text=Phone+Mount",
        },
        {
            "title": "Silicone Cable Organizer 10-Pack",
            "cost_price": 2.80, "sell_price": 14.99,
            "category": "Home Gadgets", "status": "active",
            "supplier_stock": 320, "sku": "mock-002",
            "image_url": "https://via.placeholder.com/200x200?text=Cable+Clips",
        },
        {
            "title": "Posture Corrector Back Brace",
            "cost_price": 7.20, "sell_price": 34.99,
            "category": "Health & Fitness", "status": "testing",
            "supplier_stock": 78, "sku": "mock-003",
            "image_url": "https://via.placeholder.com/200x200?text=Posture+Brace",
        },
        {
            "title": "Pet Self-Cleaning Slicker Brush",
            "cost_price": 5.50, "sell_price": 29.99,
            "category": "Pet Accessories", "status": "active",
            "supplier_stock": 210, "sku": "mock-004",
            "image_url": "https://via.placeholder.com/200x200?text=Pet+Brush",
        },
    ]

    for pd in demo_products:
        p = Product(supplier_id=supplier.id, **pd)
        p.margin_pct = p.margin()
        db.session.add(p)

    db.session.commit()

    # Seed analytics metrics
    from .agents.analytics import AnalyticsAgent
    from datetime import date, timedelta
    agent = AnalyticsAgent(app)
    agent._seed_demo_metrics(date.today() - timedelta(days=1))

    # Seed product research
    from .agents.product_research import _seed_mock_research
    _seed_mock_research()

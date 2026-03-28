"""
MarketingContentAgent — triggered when new product added.
Industry secret: Problem-Agitate-Solution (PAS) framework converts 3x better
than feature-listing copy.
"""
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MarketingContentAgent(BaseAgent):
    name = "MarketingContentAgent"

    def execute(self) -> str:
        from ..database import db
        from ..models.product import Product
        from ..integrations.claude_ai import generate_product_content

        # Find products without generated content
        products = Product.query.filter(
            (Product.ad_copy == None) | (Product.ad_copy == ""),  # noqa: E711
            Product.status.in_(["active", "testing"]),
        ).limit(10).all()

        generated = 0
        for product in products:
            content = generate_product_content(
                product_title=product.title,
                product_description=product.description or "",
                cost_price=product.cost_price,
                sell_price=product.sell_price,
            )

            import json
            product.ad_copy = json.dumps(content.get("ad_copies", []))
            product.seo_description = content.get("seo_description", "")

            # Store full content as JSON in description if no description yet
            if not product.description:
                product.description = content.get("seo_description", "")

            db.session.commit()
            generated += 1
            logger.info("Generated content for '%s'", product.title)

        return f"Generated marketing content for {generated} products"

    def generate_for_product(self, product_id):
        """Generate content for a specific product (callable from API)."""
        from ..database import db
        from ..models.product import Product
        from ..integrations.claude_ai import generate_product_content
        import json

        with self.app.app_context():
            product = Product.query.get(product_id)
            if not product:
                return None

            content = generate_product_content(
                product_title=product.title,
                product_description=product.description or "",
                cost_price=product.cost_price,
                sell_price=product.sell_price,
            )
            product.ad_copy = json.dumps(content.get("ad_copies", []))
            product.seo_description = content.get("seo_description", "")
            db.session.commit()
            return content

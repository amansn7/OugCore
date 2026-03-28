"""
Anthropic Claude API wrapper.
Used by MarketingContentAgent and CustomerServiceAgent.
Model: claude-haiku-4-5-20251001 (most cost-efficient).
"""
import logging

logger = logging.getLogger(__name__)


def generate_product_content(product_title, product_description, cost_price, sell_price):
    """
    Generate marketing content for a product using Claude.
    Uses Problem-Agitate-Solution framework (converts 3x better than features).
    Returns dict with seo_description, ad_copies, email_subjects, social_captions, faq.
    """
    from flask import current_app
    import anthropic

    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    model = current_app.config.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — returning placeholder content")
        return _placeholder_content(product_title)

    prompt = f"""You are an expert e-commerce copywriter specializing in dropshipping stores.
Generate marketing content for this product using the Problem-Agitate-Solution (PAS) framework.

Product: {product_title}
Description: {product_description or 'N/A'}
Cost: ${cost_price:.2f} | Sell Price: ${sell_price:.2f}

Return ONLY valid JSON with these exact keys:
{{
  "seo_description": "150-200 word SEO product description using PAS framework",
  "ad_copies": ["30-word ad 1", "30-word ad 2", "30-word ad 3"],
  "email_subjects": ["subject 1", "subject 2", "subject 3", "subject 4", "subject 5"],
  "social_captions": ["caption 1", "caption 2", "caption 3"],
  "faq": [
    {{"question": "Q1", "answer": "A1"}},
    {{"question": "Q2", "answer": "A2"}},
    {{"question": "Q3", "answer": "A3"}}
  ]
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as exc:
        logger.warning("Claude content generation failed: %s", exc)
        return _placeholder_content(product_title)


def generate_customer_reply(customer_email_body, product_context, intent):
    """
    Generate a customer service reply using Claude.
    Intent: WISMO | refund_request | product_question | complaint
    """
    from flask import current_app
    import anthropic

    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    model = current_app.config.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    if not api_key:
        return _default_reply(intent)

    prompt = f"""You are a helpful, empathetic customer service agent for an online store.
Customer email: {customer_email_body}
Intent detected: {intent}
Product context: {product_context or 'N/A'}

Write a concise, friendly reply (max 3 paragraphs). Be direct and resolve the issue clearly.
Do not use hollow phrases like "I hope this email finds you well".
"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        logger.warning("Claude CS reply failed: %s", exc)
        return _default_reply(intent)


def generate_analytics_summary(metrics_dict):
    """Generate a plain-English weekly business report from metrics data."""
    from flask import current_app
    import anthropic

    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    model = current_app.config.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    if not api_key:
        return "Analytics summary unavailable — set ANTHROPIC_API_KEY."

    prompt = f"""You are a business analyst for a dropshipping store.
Here are this week's metrics: {metrics_dict}

Write a concise 3-paragraph business summary:
1. What went well (highlight wins)
2. What needs attention (flag problems)
3. Top 2 action items for next week

Be direct, data-driven, and actionable. No fluff."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        logger.warning("Claude analytics summary failed: %s", exc)
        return f"Summary unavailable: {exc}"


def _placeholder_content(title):
    return {
        "seo_description": f"Discover the {title} — the solution you've been looking for. "
                           f"Order today and experience the difference.",
        "ad_copies": [
            f"Tired of the problem? {title} fixes it instantly.",
            f"Join thousands who love the {title}. Get yours today.",
            f"Limited stock: {title} — the upgrade your life needs.",
        ],
        "email_subjects": [
            f"Your {title} is waiting",
            f"Don't miss out on {title}",
            f"This solves everything 👇",
            f"Inside: how {title} changes your day",
            f"Last chance — {title} selling fast",
        ],
        "social_captions": [
            f"This {title} literally changed my life 🙌",
            f"POV: you finally found {title} ✨",
            f"Why didn't I find {title} sooner? 😭",
        ],
        "faq": [
            {"question": "How long does shipping take?", "answer": "7-14 business days."},
            {"question": "What is your return policy?", "answer": "30-day money-back guarantee."},
            {"question": "Is this product high quality?", "answer": "Yes — all products are quality-checked."},
        ],
    }


def _default_reply(intent):
    replies = {
        "WISMO": "Thank you for reaching out! Your order is on its way. "
                 "You'll receive a tracking update within 24 hours.",
        "refund_request": "We're sorry to hear that. We've initiated your refund — "
                          "please allow 3-5 business days for it to appear.",
        "product_question": "Great question! Please reply with your specific query "
                            "and we'll get back to you within 24 hours.",
        "complaint": "We sincerely apologize for the experience. Our team will "
                     "review this and contact you within 24 hours with a resolution.",
    }
    return replies.get(intent, "Thank you for contacting us. We'll respond within 24 hours.")

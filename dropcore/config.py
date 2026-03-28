import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dropcore.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CJDropshipping
    CJ_EMAIL = os.environ.get("CJ_EMAIL", "")
    CJ_PASSWORD = os.environ.get("CJ_PASSWORD", "")
    CJ_API_KEY = os.environ.get("CJ_API_KEY", "")

    # WooCommerce
    WC_URL = os.environ.get("WC_URL", "")
    WC_KEY = os.environ.get("WC_CONSUMER_KEY", "")
    WC_SECRET = os.environ.get("WC_CONSUMER_SECRET", "")

    # Claude / Anthropic
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = "claude-haiku-4-5-20251001"

    # Email (Brevo SMTP)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp-relay.brevo.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@yourstore.com")
    EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "YourStore")

    # Slack
    SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

    # Demo mode — uses mock data instead of real APIs
    DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"

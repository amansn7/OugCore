"""
Notification utility — sends alerts to Slack webhook (free) or logs them.
"""
import logging
import httpx

logger = logging.getLogger(__name__)

_webhook_url = None
_app = None


def init_notifications(app):
    global _webhook_url, _app
    _app = app
    _webhook_url = app.config.get("SLACK_WEBHOOK_URL", "")


def notify(message, level="info"):
    """
    Send a notification. If Slack webhook configured, posts there.
    Always logs to application logger.
    """
    if level == "warning":
        logger.warning("[NOTIFY] %s", message)
    else:
        logger.info("[NOTIFY] %s", message)

    if _webhook_url:
        _send_slack(message, level)


def _send_slack(message, level="info"):
    emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}.get(level, "ℹ️")
    try:
        httpx.post(
            _webhook_url,
            json={"text": f"{emoji} {message}"},
            timeout=5,
        )
    except Exception as exc:
        logger.debug("Slack notification failed: %s", exc)

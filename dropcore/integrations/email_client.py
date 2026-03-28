"""
Email client using Brevo (formerly Sendinblue) free SMTP.
Free tier: 300 emails/day — enough for order confirmations + alerts.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_email(to_address, subject, html_body, app=None):
    """Send a single transactional email via SMTP."""
    if app:
        config = app.config
    else:
        from flask import current_app
        config = current_app.config

    smtp_host = config.get("SMTP_HOST", "")
    smtp_port = config.get("SMTP_PORT", 587)
    smtp_user = config.get("SMTP_USER", "")
    smtp_pass = config.get("SMTP_PASSWORD", "")
    from_addr = config.get("EMAIL_FROM", "noreply@yourstore.com")
    from_name = config.get("EMAIL_FROM_NAME", "YourStore")

    if not smtp_user or not smtp_pass:
        logger.info("[EMAIL MOCK] To: %s | Subject: %s", to_address, subject)
        return True  # Mock success in demo mode

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_address
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, to_address, msg.as_string())
        logger.info("Email sent to %s: %s", to_address, subject)
        return True
    except Exception as exc:
        logger.error("Email send failed to %s: %s", to_address, exc)
        return False


def send_order_confirmation(order, app=None):
    subject = f"Order Confirmed — #{order.store_order_id}"
    html = f"""
    <h2>Thank you for your order!</h2>
    <p>Hi {order.customer_name or 'there'},</p>
    <p>Your order <strong>#{order.store_order_id}</strong> has been confirmed and is being processed.</p>
    <p>We'll send you a shipping notification with tracking details within 24-48 hours.</p>
    <p>Questions? Reply to this email.</p>
    """
    return send_email(order.customer_email, subject, html, app)


def send_tracking_notification(order, app=None):
    subject = f"Your Order #{order.store_order_id} Has Shipped!"
    html = f"""
    <h2>Your order is on the way!</h2>
    <p>Hi {order.customer_name or 'there'},</p>
    <p>Great news — your order <strong>#{order.store_order_id}</strong> has been shipped.</p>
    <p><strong>Tracking number:</strong> {order.tracking_number}</p>
    <p>Estimated delivery: 7-14 business days.</p>
    """
    return send_email(order.customer_email, subject, html, app)


def send_alert(subject, body, app=None):
    """Send an internal alert email to store owner."""
    if app:
        to = app.config.get("EMAIL_FROM", "")
    else:
        from flask import current_app
        to = current_app.config.get("EMAIL_FROM", "")
    if to:
        return send_email(to, f"[ALERT] {subject}", f"<pre>{body}</pre>", app)
    return False

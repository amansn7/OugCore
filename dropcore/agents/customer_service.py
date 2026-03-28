"""
CustomerServiceAgent — polls every 10 minutes.
Industry secret: proactive WISMO elimination = 70% fewer support tickets.
Auto-refund within 30 days = keeps customers happy, reduces chargebacks.
"""
import logging
import re
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Intent classification keywords
INTENT_PATTERNS = {
    "WISMO": [
        r"where.*(is|are).*order", r"tracking", r"shipped", r"delivery",
        r"when.*arrive", r"status.*order", r"order.*status",
    ],
    "refund_request": [
        r"refund", r"return", r"money back", r"cancel", r"don't want",
        r"wrong item", r"not working", r"broken", r"damaged",
    ],
    "complaint": [
        r"terrible", r"awful", r"disgusting", r"scam", r"fraud",
        r"report", r"lawsuit", r"horrible", r"worst", r"never again",
    ],
}


class CustomerServiceAgent(BaseAgent):
    name = "CustomerServiceAgent"

    def execute(self) -> str:
        # In production: connect via IMAP to check inbox
        # In demo mode: process any pending mock inquiries
        from flask import current_app
        if current_app.config.get("DEMO_MODE", True):
            return self._process_mock_inquiries()
        return self._process_imap_inbox()

    def _process_mock_inquiries(self) -> str:
        """Simulate handling customer emails in demo mode."""
        mock_emails = [
            ("customer1@example.com", "Where is my order #1234?", None),
            ("customer2@example.com", "I want a refund, the item is broken", None),
            ("customer3@example.com", "Does this product work for large dogs?", None),
        ]
        handled = 0
        for email, body, order in mock_emails:
            intent = self._classify_intent(body)
            reply = self._generate_reply(body, intent, order)
            logger.info("[CS MOCK] %s → %s: %s", email, intent, reply[:60])
            handled += 1
        return f"Handled {handled} customer inquiries (demo mode)"

    def _process_imap_inbox(self) -> str:
        """Connect to IMAP and process real customer emails."""
        import imaplib
        import email as email_lib
        from flask import current_app

        config = current_app.config
        imap_host = config.get("IMAP_HOST", "")
        imap_user = config.get("IMAP_USER", "")
        imap_pass = config.get("IMAP_PASSWORD", "")

        if not all([imap_host, imap_user, imap_pass]):
            return "IMAP not configured — skipped"

        handled = 0
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(imap_user, imap_pass)
            mail.select("inbox")
            _, uids = mail.search(None, "UNSEEN")

            for uid in uids[0].split():
                _, data = mail.fetch(uid, "(RFC822)")
                msg = email_lib.message_from_bytes(data[0][1])
                sender = msg["From"]
                subject = msg["Subject"] or ""
                body = self._get_body(msg)

                intent = self._classify_intent(subject + " " + body)
                reply = self._generate_reply(body, intent, None)

                self._send_reply(sender, subject, reply)
                mail.store(uid, "+FLAGS", "\\Seen")
                handled += 1

            mail.logout()
        except Exception as exc:
            logger.warning("IMAP processing failed: %s", exc)

        return f"Processed {handled} customer emails"

    def _classify_intent(self, text):
        """Classify email intent using regex patterns."""
        text_lower = text.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        return "product_question"

    def _generate_reply(self, body, intent, order):
        """Generate reply — escalate complaints, auto-handle the rest."""
        from ..integrations.claude_ai import generate_customer_reply

        product_context = None
        if order:
            product_context = f"Order #{order.store_order_id}, status: {order.status}"

        if intent == "complaint":
            self._escalate_to_human(body, intent)
            return "Escalated to human support team."

        return generate_customer_reply(body, product_context, intent)

    def _escalate_to_human(self, body, intent):
        """Send Slack alert for complaints that need human review."""
        from ..utils.notifications import notify
        notify(f"[CS ESCALATION] {intent}: {body[:200]}", level="warning")

    def _get_body(self, msg):
        """Extract plain text from email message."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore") if msg.get_payload() else ""

    def _send_reply(self, to, subject, body):
        """Send reply via SMTP."""
        from ..integrations.email_client import send_email
        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        send_email(to, reply_subject, f"<p>{body}</p>")

import time
import logging
from datetime import datetime, timezone
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all DropCore agents.
    Handles: logging to DB, retry logic, error recovery, timing.
    """

    name: str = "BaseAgent"

    def __init__(self, app=None):
        self.app = app

    def run(self):
        """Entry point — wraps execute() with timing, logging, and error handling."""
        from ..database import db
        from ..models.agent_log import AgentLog

        start = time.time()
        log = AgentLog(agent_name=self.name, status="info", message="Starting")
        try:
            with self.app.app_context():
                db.session.add(log)
                db.session.commit()

                result = self.execute()
                elapsed = int((time.time() - start) * 1000)

                log.status = "success"
                log.message = result or f"{self.name} completed"
                log.duration_ms = elapsed
                db.session.commit()

                logger.info("[%s] completed in %dms: %s", self.name, elapsed, log.message)
                return log.message

        except Exception as exc:
            elapsed = int((time.time() - start) * 1000)
            logger.exception("[%s] failed: %s", self.name, exc)
            try:
                with self.app.app_context():
                    log.status = "error"
                    log.message = str(exc)
                    log.duration_ms = elapsed
                    db.session.commit()
            except Exception:
                pass
            return f"ERROR: {exc}"

    @abstractmethod
    def execute(self) -> str:
        """Override in each agent subclass. Return a short status string."""
        pass

    def _retry(self, fn, retries=3, backoff=2):
        """Call fn() with exponential backoff on failure."""
        for attempt in range(retries):
            try:
                return fn()
            except Exception as exc:
                if attempt == retries - 1:
                    raise
                wait = backoff ** attempt
                logger.warning("[%s] retry %d/%d after %ds: %s", self.name, attempt + 1, retries, wait, exc)
                time.sleep(wait)

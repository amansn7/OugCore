import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler():
    global _scheduler
    return _scheduler


def init_scheduler(app):
    global _scheduler
    from .agents import (
        ProductResearchAgent,
        PriceMonitorAgent,
        OrderFulfillmentAgent,
        CustomerServiceAgent,
        InventoryMonitorAgent,
        AnalyticsAgent,
    )

    _scheduler = BackgroundScheduler(daemon=True)

    agents = {
        "product_research": ProductResearchAgent(app),
        "price_monitor": PriceMonitorAgent(app),
        "order_fulfillment": OrderFulfillmentAgent(app),
        "customer_service": CustomerServiceAgent(app),
        "inventory_monitor": InventoryMonitorAgent(app),
        "analytics": AnalyticsAgent(app),
    }

    # Product research: daily at 6am
    _scheduler.add_job(
        agents["product_research"].run,
        CronTrigger(hour=6, minute=0),
        id="product_research",
        replace_existing=True,
    )

    # Price monitoring: every 6 hours
    _scheduler.add_job(
        agents["price_monitor"].run,
        IntervalTrigger(hours=6),
        id="price_monitor",
        replace_existing=True,
    )

    # Order fulfillment: every 15 minutes
    _scheduler.add_job(
        agents["order_fulfillment"].run,
        IntervalTrigger(minutes=15),
        id="order_fulfillment",
        replace_existing=True,
    )

    # Customer service: every 10 minutes (IMAP poll)
    _scheduler.add_job(
        agents["customer_service"].run,
        IntervalTrigger(minutes=10),
        id="customer_service",
        replace_existing=True,
    )

    # Inventory monitor: every 2 hours
    _scheduler.add_job(
        agents["inventory_monitor"].run,
        IntervalTrigger(hours=2),
        id="inventory_monitor",
        replace_existing=True,
    )

    # Analytics: daily at 11pm
    _scheduler.add_job(
        agents["analytics"].run,
        CronTrigger(hour=23, minute=0),
        id="analytics_daily",
        replace_existing=True,
    )

    # Analytics weekly report: every Sunday at 8am
    _scheduler.add_job(
        agents["analytics"].run,
        CronTrigger(day_of_week="sun", hour=8, minute=0),
        id="analytics_weekly",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("DropCore scheduler started with %d jobs", len(_scheduler.get_jobs()))
    return _scheduler, agents

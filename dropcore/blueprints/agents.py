"""Agents blueprint — control panel for viewing and triggering agents."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app

bp = Blueprint("agents_bp", __name__, url_prefix="/dashboard/agents")

AGENT_REGISTRY = {
    "product_research": "ProductResearchAgent",
    "price_monitor": "PriceMonitorAgent",
    "order_fulfillment": "OrderFulfillmentAgent",
    "customer_service": "CustomerServiceAgent",
    "marketing_content": "MarketingContentAgent",
    "inventory_monitor": "InventoryMonitorAgent",
    "analytics": "AnalyticsAgent",
}

AGENT_DESCRIPTIONS = {
    "product_research": "Discovers trending products from Google Trends + AliExpress. Runs daily at 6am.",
    "price_monitor": "Monitors competitor prices and suggests repricing. Runs every 6 hours.",
    "order_fulfillment": "Auto-fulfills new orders via CJDropshipping. Runs every 15 minutes.",
    "customer_service": "Handles customer emails: WISMO, refunds, questions. Runs every 10 minutes.",
    "marketing_content": "Generates SEO descriptions and ad copy using Claude AI. Triggered on new products.",
    "inventory_monitor": "Monitors supplier stock, hides low-stock products. Runs every 2 hours.",
    "analytics": "Calculates daily KPIs and detects anomalies. Runs daily at 11pm.",
}


@bp.route("/")
def index():
    from ..models.agent_log import AgentLog
    from ..scheduler import get_scheduler

    logs = AgentLog.query.order_by(AgentLog.run_at.desc()).limit(50).all()
    scheduler = get_scheduler()
    jobs = []
    if scheduler:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else "N/A",
            })

    return render_template(
        "dashboard/agents.html",
        logs=logs,
        jobs=jobs,
        agent_registry=AGENT_REGISTRY,
        agent_descriptions=AGENT_DESCRIPTIONS,
    )


@bp.route("/run/<agent_key>", methods=["POST"])
def run_agent(agent_key):
    """Manually trigger an agent run."""
    if agent_key not in AGENT_REGISTRY:
        return jsonify({"error": "Unknown agent"}), 404

    from .. import agents as agent_module
    agent_class = getattr(agent_module, AGENT_REGISTRY[agent_key], None)
    if not agent_class:
        return jsonify({"error": "Agent not found"}), 404

    app = current_app._get_current_object()
    agent = agent_class(app)

    import threading
    t = threading.Thread(target=agent.run, daemon=True)
    t.start()

    return jsonify({"status": "started", "agent": agent_key})


@bp.route("/logs/json")
def logs_json():
    from ..models.agent_log import AgentLog
    agent = request.args.get("agent", "")
    query = AgentLog.query.order_by(AgentLog.run_at.desc())
    if agent:
        query = query.filter_by(agent_name=agent)
    return jsonify([log.to_dict() for log in query.limit(100).all()])

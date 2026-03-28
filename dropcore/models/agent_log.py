import json
from datetime import datetime, timezone
from ..database import db


class AgentLog(db.Model):
    __tablename__ = "agent_logs"

    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(100), nullable=False)
    run_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # success | error | warning | info
    status = db.Column(db.String(20), default="info")
    message = db.Column(db.Text)
    data_json = db.Column(db.Text)  # JSON string of extra context
    duration_ms = db.Column(db.Integer, default=0)

    def set_data(self, data: dict):
        self.data_json = json.dumps(data)

    def get_data(self) -> dict:
        if self.data_json:
            return json.loads(self.data_json)
        return {}

    def to_dict(self):
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "run_at": self.run_at.isoformat(),
            "status": self.status,
            "message": self.message,
            "duration_ms": self.duration_ms,
        }

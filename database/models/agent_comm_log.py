"""
SQLAlchemy Model for Agent Communication Protocol Logs
"""

from sqlalchemy import Column, String, Integer, JSON, DateTime, Index
from datetime import datetime

# Import Base from parent models.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Base


class AgentCommLog(Base):
    """Database model for ACP message logs"""
    __tablename__ = "agent_comm_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(64), unique=True, nullable=False, index=True)
    version = Column(String(8), nullable=False, default="1.1")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    type = Column(String(32), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=2)
    content = Column(JSON, nullable=False)
    targets = Column(JSON, nullable=False)
    context = Column(JSON, nullable=False)
    correlation_id = Column(String(64), nullable=True, index=True)
    ttl_seconds = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_agent_session', 'agent_id', 'session_id'),
        Index('idx_type_timestamp', 'type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AgentCommLog {self.message_id} {self.type} from {self.agent_id}>"

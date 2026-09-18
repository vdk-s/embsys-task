from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # New fields for Jira-like task management
    status = Column(String, nullable=True, default="To Do", server_default="To Do")
    priority = Column(String, nullable=True, default="Medium", server_default="Medium")
    assigned_to = Column(String, nullable=True)


from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from datetime import datetime

# Valid choices
STATUS_CHOICES = Literal["To Do", "In Progress", "Done"]
PRIORITY_CHOICES = Literal["Low", "Medium", "High"]


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    status: STATUS_CHOICES = "To Do"
    priority: PRIORITY_CHOICES = "Medium"
    assigned_to: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    status: Optional[STATUS_CHOICES] = None
    priority: Optional[PRIORITY_CHOICES] = None
    assigned_to: Optional[str] = None


class Task(TaskBase):
    id: int
    created_at: datetime

    # Pydantic v2 configuration to map from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class Employee(BaseModel):
    id: int
    name: str

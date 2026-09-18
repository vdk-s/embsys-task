from sqlalchemy.orm import Session
from . import models, schemas
from typing import List

# Simulated team members — demo data only (no DB table needed)
TEAM_MEMBERS: List[schemas.Employee] = [
    schemas.Employee(id=1, name="Arun"),
    schemas.Employee(id=2, name="Priya"),
    schemas.Employee(id=3, name="Karthik"),
    schemas.Employee(id=4, name="Rahul"),
    schemas.Employee(id=5, name="Sneha"),
]


def get_employees() -> List[schemas.Employee]:
    """Return the list of simulated team members."""
    return TEAM_MEMBERS


def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()


def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, db_task: models.Task, task_update: schemas.TaskUpdate):
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: models.Task):
    db.delete(db_task)
    db.commit()
    return db_task

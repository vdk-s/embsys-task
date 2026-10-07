from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# Initial team members seed data
INITIAL_TEAM_MEMBERS = [
    {"name": "S Venkata Diwakar (Team Leader)", "role": "Team Leader"},
    {"name": "T Sam Sherwin", "role": "Member"},
    {"name": "R Saran", "role": "Member"},
    {"name": "Sangeeth", "role": "Member"},
    {"name": "Shijo", "role": "Member"},
]


def seed_employees_if_empty(db: Session) -> None:
    """Seed the database with initial team members if the table is empty."""
    count = db.query(models.Employee).count()
    if count == 0:
        for member in INITIAL_TEAM_MEMBERS:
            db.add(models.Employee(**member))
        db.commit()


def get_employees(db: Session) -> List[models.Employee]:
    """Return all team members from the database."""
    return db.query(models.Employee).order_by(models.Employee.id.asc()).all()


def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """Retrieve an employee by their ID."""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()


def create_employee(db: Session, employee: schemas.EmployeeCreate) -> models.Employee:
    """Add a new employee to the database."""
    db_employee = models.Employee(
        name=employee.name.strip(),
        role=employee.role.strip() if employee.role else None,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, db_employee: models.Employee) -> models.Employee:
    """Delete an employee from the database."""
    db.delete(db_employee)
    db.commit()
    return db_employee


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

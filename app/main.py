from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import os

from . import models, schemas, crud
from .database import engine, SessionLocal

# Create database tables (new tables; existing ones untouched by create_all)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API")

# CORS — allow all origins so the frontend can call the API during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_migrations():
    """
    Safe SQLite and PostgreSQL migration: check existing columns,
    then add columns if missing (status, priority, assigned_to).
    """
    new_columns = {
        "status": "VARCHAR DEFAULT 'To Do'",
        "priority": "VARCHAR DEFAULT 'Medium'",
        "assigned_to": "VARCHAR",
    }

    backend = engine.url.get_backend_name()

    try:
        if backend == "sqlite":
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(tasks)"))
                existing_columns = {row[1] for row in result.fetchall()}

                for col_name, col_def in new_columns.items():
                    if col_name not in existing_columns:
                        conn.execute(
                            text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}")
                        )
                        conn.commit()
        elif backend == "postgresql":
            with engine.connect() as conn:
                for col_name, col_def in new_columns.items():
                    conn.execute(
                        text(f"ALTER TABLE tasks ADD COLUMN IF NOT EXISTS {col_name} {col_def}")
                    )
                conn.commit()
    except Exception as e:
        # Log note but don't fail startup if columns already exist or table is fresh
        print(f"Migration note: {e}")


# Run migration and seeding at startup
run_migrations()

def seed_initial_data():
    db = SessionLocal()
    try:
        crud.seed_employees_if_empty(db)
    except Exception as e:
        print(f"Seed note: {e}")
    finally:
        db.close()

seed_initial_data()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Employee endpoints
# ---------------------------------------------------------------------------

@app.get("/employees", response_model=List[schemas.Employee])
@app.get("/employees/", response_model=List[schemas.Employee], include_in_schema=False)
def get_employees(db: Session = Depends(get_db)):
    """Return the list of team members from the database."""
    return crud.get_employees(db)


@app.post("/employees", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED)
@app.post("/employees/", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    """Add a new team member to the database."""
    if not employee.name or not employee.name.strip():
        raise HTTPException(status_code=422, detail="Employee name cannot be empty")
    return crud.create_employee(db=db, employee=employee)


@app.delete("/employees/{employee_id}", response_model=schemas.Employee)
@app.delete("/employees/{employee_id}/", response_model=schemas.Employee, include_in_schema=False)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete a team member by their ID."""
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp_data = schemas.Employee.model_validate(db_employee)
    crud.delete_employee(db=db, db_employee=db_employee)
    return emp_data


# Alias endpoints for /members
@app.get("/members", response_model=List[schemas.Employee], include_in_schema=False)
@app.get("/members/", response_model=List[schemas.Employee], include_in_schema=False)
def get_members(db: Session = Depends(get_db)):
    return crud.get_employees(db)


@app.post("/members", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/members/", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_member(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return create_employee(employee=employee, db=db)


@app.delete("/members/{member_id}", response_model=schemas.Employee, include_in_schema=False)
@app.delete("/members/{member_id}/", response_model=schemas.Employee, include_in_schema=False)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    return delete_employee(employee_id=member_id, db=db)



# ---------------------------------------------------------------------------
# Task endpoints (all existing endpoints preserved exactly)
# ---------------------------------------------------------------------------

@app.post("/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)


@app.get("/tasks", response_model=List[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    return tasks


@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return crud.update_task(db=db, db_task=db_task, task_update=task)


@app.delete("/tasks/{task_id}", response_model=schemas.Task)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Store data before it's deleted and expired by SQLAlchemy commit
    task_data = schemas.Task.model_validate(db_task)
    crud.delete_task(db=db, db_task=db_task)
    return task_data


# ---------------------------------------------------------------------------
# Serve frontend static files (must be mounted last so API routes take priority)
# ---------------------------------------------------------------------------
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

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
    Safe SQLite migration: check PRAGMA table_info to discover existing columns,
    then issue ALTER TABLE ... ADD COLUMN only for columns that are missing.
    Does NOT use 'ADD COLUMN IF NOT EXISTS' (not supported by all SQLite versions).
    """
    new_columns = {
        "status": "VARCHAR DEFAULT 'To Do'",
        "priority": "VARCHAR DEFAULT 'Medium'",
        "assigned_to": "VARCHAR",
    }

    with engine.connect() as conn:
        # Fetch existing column names from the tasks table
        result = conn.execute(text("PRAGMA table_info(tasks)"))
        existing_columns = {row[1] for row in result.fetchall()}

        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                conn.execute(
                    text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}")
                )
                conn.commit()


# Run migration at startup
run_migrations()


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
def get_employees():
    """Return the list of simulated team members."""
    return crud.get_employees()


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

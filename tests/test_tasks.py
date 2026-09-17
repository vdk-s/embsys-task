import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.database import Base

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after each test to ensure tests are independent
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_create_task(client):
    response = client.post("/tasks", json={"title": "Test Task", "description": "This is a test"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "This is a test"
    assert data["completed"] is False
    assert "id" in data

def test_read_tasks(client):
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})
    
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"

def test_read_existing_task(client):
    create_response = client.post("/tasks", json={"title": "Test Task"})
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task"

def test_read_invalid_task(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}

def test_update_existing_task(client):
    create_response = client.post("/tasks", json={"title": "Old Task"})
    task_id = create_response.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"title": "Updated Task", "completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Updated Task"
    assert data["completed"] is True

def test_delete_existing_task(client):
    create_response = client.post("/tasks", json={"title": "Task to Delete"})
    task_id = create_response.json()["id"]

    # Delete task
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Task to Delete"

    # Verify it is deleted
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

def test_delete_invalid_task(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}

def test_create_task_invalid_validation(client):
    # Missing title which is required
    response = client.post("/tasks", json={"description": "No title here"})
    assert response.status_code == 422

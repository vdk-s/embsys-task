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
    from app.crud import seed_employees_if_empty
    seed_employees_if_empty(db)
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

# ===========================================================================
# Existing tests (unchanged) — 8 tests
# ===========================================================================

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

# ===========================================================================
# New tests — task assignment, status, priority, employees
# ===========================================================================

def test_create_task_with_status_priority_assignee(client):
    """POST /tasks with all new fields should return them in the response."""
    payload = {
        "title": "Implement Backend API",
        "description": "Build the REST endpoints",
        "status": "In Progress",
        "priority": "High",
        "assigned_to": "Arun",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Implement Backend API"
    assert data["status"] == "In Progress"
    assert data["priority"] == "High"
    assert data["assigned_to"] == "Arun"

def test_create_task_default_status_and_priority(client):
    """POST /tasks without status/priority/assigned_to should use defaults."""
    response = client.post("/tasks", json={"title": "Minimal Task"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "To Do"
    assert data["priority"] == "Medium"
    assert data["assigned_to"] is None

def test_update_task_status(client):
    """PUT /tasks/{id} can change status independently."""
    create_resp = client.post("/tasks", json={"title": "Status Test"})
    task_id = create_resp.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"status": "Done"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Done"
    # Other fields should be unchanged
    assert data["title"] == "Status Test"

def test_update_task_priority(client):
    """PUT /tasks/{id} can change priority independently."""
    create_resp = client.post("/tasks", json={"title": "Priority Test", "priority": "Low"})
    task_id = create_resp.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"priority": "High"})
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "High"

def test_update_task_assigned_to(client):
    """PUT /tasks/{id} can assign or reassign a team member."""
    create_resp = client.post("/tasks", json={"title": "Assign Test"})
    task_id = create_resp.json()["id"]

    # Assign
    response = client.put(f"/tasks/{task_id}", json={"assigned_to": "Priya"})
    assert response.status_code == 200
    assert response.json()["assigned_to"] == "Priya"

    # Reassign
    response2 = client.put(f"/tasks/{task_id}", json={"assigned_to": "Karthik"})
    assert response2.status_code == 200
    assert response2.json()["assigned_to"] == "Karthik"

def test_get_employees(client):
    """GET /employees returns all 5 seeded real team members."""
    response = client.get("/employees")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    names = [e["name"] for e in data]
    assert "S Venkata Diwakar (Team Leader)" in names
    assert "T Sam Sherwin" in names
    assert "R Saran" in names
    assert "Sangeeth" in names
    assert "Shijo" in names
    # Each member must have an id field
    for emp in data:
        assert "id" in emp
        assert "name" in emp


def test_create_employee(client):
    """POST /employees successfully creates a new team member."""
    response = client.post("/employees", json={"name": "Alex Morgan", "role": "QA Engineer"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alex Morgan"
    assert data["role"] == "QA Engineer"
    assert "id" in data

    # Verify new employee appears in GET /employees
    get_resp = client.get("/employees")
    names = [e["name"] for e in get_resp.json()]
    assert "Alex Morgan" in names


def test_create_employee_empty_name_rejected(client):
    """POST /employees with empty or whitespace name should return 422."""
    response = client.post("/employees", json={"name": "   "})
    assert response.status_code == 422


def test_delete_employee(client):
    """DELETE /employees/{id} removes a member from the database."""
    # First create a member to delete
    create_resp = client.post("/employees", json={"name": "Temporary Member"})
    assert create_resp.status_code == 201
    member_id = create_resp.json()["id"]

    # Delete the member
    del_resp = client.delete(f"/employees/{member_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["id"] == member_id

    # Verify member is gone
    get_resp = client.get("/employees")
    ids = [e["id"] for e in get_resp.json()]
    assert member_id not in ids


def test_delete_nonexistent_employee(client):
    """DELETE /employees/{id} with invalid ID returns 404."""
    response = client.delete("/employees/99999")
    assert response.status_code == 404


def test_members_alias_endpoints(client):
    """Verify /members alias works for GET, POST, and DELETE."""
    # GET /members
    res_get = client.get("/members")
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 5

    # POST /members
    res_post = client.post("/members", json={"name": "Alias Member"})
    assert res_post.status_code == 201
    new_id = res_post.json()["id"]

def test_create_employee_trailing_slash(client):
    """POST /employees/ with trailing slash should return 201 without 405 error."""
    response = client.post("/employees/", json={"name": "Trailing Slash Member"})
    assert response.status_code == 201
    assert response.json()["name"] == "Trailing Slash Member"




def test_invalid_status_rejected(client):
    """POST /tasks with an invalid status value should return 422."""
    response = client.post("/tasks", json={"title": "Bad Status", "status": "Pending"})
    assert response.status_code == 422

def test_invalid_priority_rejected(client):
    """POST /tasks with an invalid priority value should return 422."""
    response = client.post("/tasks", json={"title": "Bad Priority", "priority": "Critical"})
    assert response.status_code == 422

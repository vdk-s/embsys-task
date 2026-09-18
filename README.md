# Task Management System

A Jira-like Task Management System built with FastAPI, SQLAlchemy, SQLite, and a vanilla HTML/CSS/JS frontend. The project includes automated tests, Docker support, and a GitHub Actions CI/CD pipeline that publishes to GitHub Container Registry (GHCR).

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Application language |
| FastAPI | Web framework |
| SQLAlchemy | ORM and database access |
| Pydantic v2 | Request/response validation and serialization |
| SQLite | Persistent data storage |
| Vanilla HTML/CSS/JS | Frontend (no framework) |
| Pytest | Automated testing |
| Docker | Containerization |
| Docker Compose | Local container orchestration |
| GitHub Actions | CI/CD automation |
| GitHub Container Registry (GHCR) | Docker image hosting |

---

## Project Structure

```
embsys-task/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, route definitions, SQLite migration
│   ├── crud.py          # Database CRUD operations + simulated employees
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   └── database.py      # Database engine and session setup
├── frontend/
│   ├── index.html       # Dashboard — served at http://localhost:8000/
│   ├── style.css        # Professional dark theme stylesheet
│   └── app.js           # Vanilla JS — fetch calls, filters, modals
├── tests/
│   ├── __init__.py
│   └── test_tasks.py    # Pytest unit tests (16 tests)
├── .github/
│   └── workflows/
│       └── ci-cd.yml    # GitHub Actions CI/CD workflow
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Docker Compose service configuration
├── requirements.txt     # Python dependencies
├── .dockerignore        # Files excluded from the Docker build context
└── .gitignore
```

---

## Frontend

The frontend is a single-page dashboard served directly by FastAPI at `http://localhost:8000/`.

**Features:**
- **Dashboard** with live statistics (total, to-do, in-progress, done)
- **Task table** with status badges, priority indicators, and assignee avatars
- **Create Task** modal with all fields
- **Edit Task** modal (pre-filled with current values)
- **Delete Task** with confirmation dialog
- **Real-time search** by title and description
- **Filters** by status, priority, and team member
- **Sortable columns** (click any column header)
- **Toast notifications** for create/edit/delete actions
- Responsive layout — works on desktop and tablet

**How to access the frontend:**
```
http://localhost:8000/
```

---

## Simulated Team Members

Five demo team members are built into the application for demonstration purposes. They are returned by the `GET /employees` endpoint and available in all task assignment dropdowns.

| ID | Name |
|---|---|
| 1 | Arun |
| 2 | Priya |
| 3 | Karthik |
| 4 | Rahul |
| 5 | Sneha |

These are demo/simulated members only — they are not stored in the database.

---

## Task Assignment

Tasks can be assigned to a team member via the `assigned_to` field:

```json
{
  "title": "Implement Backend API",
  "description": "Build the REST endpoints",
  "status": "In Progress",
  "priority": "High",
  "assigned_to": "Arun"
}
```

---

## Task Status

Each task supports one of three statuses:

| Status | Description |
|---|---|
| `To Do` | Default — not started |
| `In Progress` | Actively being worked on |
| `Done` | Completed |

---

## Task Priority

Each task supports one of three priority levels:

| Priority | Description |
|---|---|
| `Low` | Nice-to-have or low urgency |
| `Medium` | Default — normal priority |
| `High` | Urgent or blocking |

---

## API Endpoints

Interactive Swagger documentation is available at **`/docs`** when the application is running.

| Method | Path | Purpose | Success Status | Error Status |
|---|---|---|---|---|
| `GET` | `/employees` | List all simulated team members | `200 OK` | — |
| `POST` | `/tasks` | Create a new task | `201 Created` | `422 Unprocessable Entity` |
| `GET` | `/tasks` | Retrieve all tasks | `200 OK` | — |
| `GET` | `/tasks/{task_id}` | Retrieve a single task by ID | `200 OK` | `404 Not Found` |
| `PUT` | `/tasks/{task_id}` | Update an existing task by ID | `200 OK` | `404 Not Found` |
| `DELETE` | `/tasks/{task_id}` | Delete a task by ID | `200 OK` (returns deleted task) | `404 Not Found` |

**Example request body for `POST /tasks`:**
```json
{
  "title": "Write documentation",
  "description": "Update the project README",
  "status": "To Do",
  "priority": "Medium",
  "assigned_to": "Priya",
  "completed": false
}
```

**Example response:**
```json
{
  "id": 1,
  "title": "Write documentation",
  "description": "Update the project README",
  "completed": false,
  "status": "To Do",
  "priority": "Medium",
  "assigned_to": "Priya",
  "created_at": "2026-09-18T10:00:00.000000"
}
```

---

## Validation

Validation is handled by Pydantic v2 schemas defined in `app/schemas.py`:

- **`title`** — required string
- **`description`** — optional string, defaults to `null`
- **`completed`** — optional boolean, defaults to `false`
- **`status`** — optional, must be `"To Do"`, `"In Progress"`, or `"Done"`. Defaults to `"To Do"`. Invalid values return `422`.
- **`priority`** — optional, must be `"Low"`, `"Medium"`, or `"High"`. Defaults to `"Medium"`. Invalid values return `422`.
- **`assigned_to`** — optional string (team member name), defaults to `null`
- **`PUT /tasks/{task_id}`** — all fields are optional, allowing partial updates

---

## Testing

The test suite is located in `tests/test_tasks.py` and uses Pytest with FastAPI's `TestClient`. Tests run against a dedicated in-memory SQLite database — the production `sql_app.db` is never touched.

**Tests are isolated**: each test creates and drops its own database tables.

**Coverage (16 tests, all passing):**

| Test | Scenario |
|---|---|
| `test_create_task` | `POST /tasks` returns `201` with the created task |
| `test_read_tasks` | `GET /tasks` returns `200` with all tasks |
| `test_read_existing_task` | `GET /tasks/{task_id}` returns `200` for a valid ID |
| `test_read_invalid_task` | `GET /tasks/999` returns `404` |
| `test_update_existing_task` | `PUT /tasks/{task_id}` returns `200` with updated data |
| `test_delete_existing_task` | `DELETE /tasks/{task_id}` returns `200` and verifies deletion |
| `test_delete_invalid_task` | `DELETE /tasks/999` returns `404` |
| `test_create_task_invalid_validation` | `POST /tasks` without `title` returns `422` |
| `test_create_task_with_status_priority_assignee` | POST with all new fields returns them correctly |
| `test_create_task_default_status_and_priority` | POST without new fields uses correct defaults |
| `test_update_task_status` | PUT can change status independently |
| `test_update_task_priority` | PUT can change priority independently |
| `test_update_task_assigned_to` | PUT can assign and reassign a team member |
| `test_get_employees` | `GET /employees` returns all 5 team members with correct structure |
| `test_invalid_status_rejected` | Invalid status value returns `422` |
| `test_invalid_priority_rejected` | Invalid priority value returns `422` |

**Verified result: 16/16 tests pass.**

---

## Running Locally

### Prerequisites

- Python 3.11+

### Setup

```powershell
# Create and activate a virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Start the development server

```bash
uvicorn app.main:app --reload
```

The application is available at:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/` | **Frontend Dashboard** |
| `http://127.0.0.1:8000/docs` | **Swagger UI (API docs)** |
| `http://127.0.0.1:8000/employees` | Team members JSON |
| `http://127.0.0.1:8000/tasks` | Tasks JSON |

### Run the test suite

```bash
pytest tests/
```

---

## Running with Docker

Docker Compose builds the image, starts the container, and mounts the local `sql_app.db` file so the database is persisted between container restarts.

```bash
# Build and start the container in detached mode
docker compose up --build -d
```

| URL | Purpose |
|---|---|
| `http://localhost:8000/` | **Frontend Dashboard** |
| `http://localhost:8000/docs` | **Swagger UI** |

```bash
# Stop and remove the container
docker compose down
```

> **Note:** The application uses SQLite. There is no separate database container.

---

## CI/CD

The pipeline is defined in `.github/workflows/ci-cd.yml` and is triggered on:
- Pushes to the `main` branch
- Pull requests targeting `main`

### CI Job — runs on every push and pull request

1. Checks out the repository
2. Sets up Python 3.11
3. Installs dependencies from `requirements.txt`
4. Runs `flake8` linting (hard fail on syntax errors and undefined names)
5. Runs `pytest tests/`
6. Performs a test `docker build` to verify the Dockerfile

### CD Job — runs only on push to `main` (after CI passes)

1. Logs in to GitHub Container Registry using the built-in `GITHUB_TOKEN`
2. Extracts Docker metadata (tags and labels)
3. Builds and pushes the Docker image to GHCR

The workflow uses `permissions: packages: write` scoped only to the CD job. No personal access tokens or hardcoded credentials are used.

---

## Docker Image (GHCR)

The Docker image is published to GitHub Container Registry on every successful push to `main`.

**Image:** `ghcr.io/vdk-s/embsys-task`

**Tags produced per push:**
- `latest` — always points to the most recent build from `main`
- `sha-<short-git-sha>` — pinned tag for a specific commit (e.g., `sha-a1b2c3d`)

**Pull the latest image:**
```bash
docker pull ghcr.io/vdk-s/embsys-task:latest
```

---

## Git Workflow

The project is version-controlled with Git and hosted on GitHub. CI/CD is triggered automatically by GitHub Actions on each push.

---

## Submission Summary

| Requirement | Status |
|---|---|
| CRUD REST API (FastAPI) | ✅ Complete |
| Database persistence (SQLite + SQLAlchemy) | ✅ Complete |
| Request/response validation (Pydantic v2) | ✅ Complete |
| Automated unit tests (Pytest, 16/16 passing) | ✅ Complete |
| Docker containerisation | ✅ Complete |
| Docker Compose | ✅ Complete |
| GitHub Actions CI/CD pipeline | ✅ Complete |
| Docker image published to GHCR | ✅ Complete |
| Frontend (vanilla HTML/CSS/JS dashboard) | ✅ Complete |
| Task status (To Do / In Progress / Done) | ✅ Complete |
| Task priority (Low / Medium / High) | ✅ Complete |
| Task assignment (assigned_to field) | ✅ Complete |
| Simulated team members (`GET /employees`) | ✅ Complete |
| Safe SQLite migration (PRAGMA table_info) | ✅ Complete |
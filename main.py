import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent / "todo.db"))

APP_USERNAME = os.environ.get("APP_USERNAME")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

if not APP_USERNAME or not APP_PASSWORD:
    raise RuntimeError(
        "APP_USERNAME and APP_PASSWORD environment variables must be set"
    )

basic_auth = HTTPBasic()


def require_auth(credentials: HTTPBasicCredentials = Depends(basic_auth)):
    valid_username = secrets.compare_digest(credentials.username, APP_USERNAME)
    valid_password = secrets.compare_digest(credentials.password, APP_PASSWORD)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


app = FastAPI(title="To-Do List API", dependencies=[Depends(require_auth)])


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0,
                due_date TEXT
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        if "due_date" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class TaskCreate(BaseModel):
    title: str
    done: bool = False
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None
    due_date: Optional[date] = None


class Task(BaseModel):
    id: int
    title: str
    done: bool
    due_date: Optional[date] = None


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/tasks", response_model=list[Task])
def list_tasks():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, done, due_date FROM tasks ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done, due_date) VALUES (?, ?, ?)",
            (task.title, task.done, task.due_date.isoformat() if task.due_date else None),
        )
        row = conn.execute(
            "SELECT id, title, done, due_date FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, title, done, due_date FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")

        # exclude_unset lets clients omit a field to keep it unchanged, while an
        # explicit `null` (e.g. due_date) clears it.
        updates = task.model_dump(exclude_unset=True)
        new_title = updates.get("title", existing["title"])
        new_done = updates.get("done", existing["done"])
        new_due_date = updates.get("due_date", existing["due_date"])
        if isinstance(new_due_date, date):
            new_due_date = new_due_date.isoformat()

        conn.execute(
            "UPDATE tasks SET title = ?, done = ?, due_date = ? WHERE id = ?",
            (new_title, new_done, new_due_date, task_id),
        )
        row = conn.execute(
            "SELECT id, title, done, due_date FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return dict(row)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return None


@app.get("/")
def serve_index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

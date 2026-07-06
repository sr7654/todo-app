import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = Path(__file__).parent / "todo.db"

app = FastAPI(title="To-Do List API")


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0
            )
            """
        )


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


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


class Task(BaseModel):
    id: int
    title: str
    done: bool


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/tasks", response_model=list[Task])
def list_tasks():
    with get_db() as conn:
        rows = conn.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
        return [dict(row) for row in rows]


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, task.done)
        )
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")

        new_title = task.title if task.title is not None else existing["title"]
        new_done = task.done if task.done is not None else existing["done"]

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
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


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

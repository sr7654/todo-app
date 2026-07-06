# To-Do List App

A simple to-do list app with a FastAPI backend, SQLite database, and a minimal HTML/JS frontend. Supports creating, listing, updating, and deleting tasks, each with an optional due date.

## Requirements

- Python 3.9+

## Setup

```bash
cd todo-app
pip install -r requirements.txt
```

## Start

```bash
uvicorn main:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser. The SQLite database (`todo.db`) is created automatically on first run.

## Stop

Press `Ctrl+C` in the terminal running the server.

## API

| Method | Endpoint          | Description                          |
|--------|-------------------|---------------------------------------|
| GET    | `/api/tasks`      | List all tasks                        |
| POST   | `/api/tasks`      | Create a task                         |
| PUT    | `/api/tasks/{id}` | Update a task (title, done, due_date) |
| DELETE | `/api/tasks/{id}` | Delete a task                         |

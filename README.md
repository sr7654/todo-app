# To-Do List App

A simple to-do list app with a FastAPI backend, SQLite database, and a minimal HTML/JS frontend. Supports creating, listing, updating, and deleting tasks, each with an optional due date.

## Requirements

- Python 3.9+

## Setup

```bash
cd todo-app
pip install -r requirements.txt
```

The app is protected with HTTP Basic Auth. Set credentials via environment variables before starting it — the app will refuse to start without them:

```bash
export APP_USERNAME=admin
export APP_PASSWORD=change-me
```

(On Windows PowerShell: `$env:APP_USERNAME = "admin"`, `$env:APP_PASSWORD = "change-me"`.)

## Start

```bash
uvicorn main:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser — your browser will prompt for the username/password set above. The SQLite database (`todo.db` locally, or the path in `DB_PATH` if set) is created automatically on first run.

## Stop

Press `Ctrl+C` in the terminal running the server.

## Deploying to Fly.io

This repo includes a `Dockerfile` and `fly.toml` for deploying to [Fly.io](https://fly.io), which persists the SQLite file on a mounted volume at `/data`.

```bash
fly launch --no-deploy        # edit the generated app name in fly.toml if prompted
fly volumes create todo_data --size 1 --region iad
fly secrets set APP_USERNAME=admin APP_PASSWORD=change-me
fly deploy
```

`fly launch` may overwrite `fly.toml` — re-add the `[mounts]` block (`source = "todo_data"`, `destination = "/data"`) if it's missing before deploying.

## API

| Method | Endpoint          | Description                          |
|--------|-------------------|---------------------------------------|
| GET    | `/api/tasks`      | List all tasks                        |
| POST   | `/api/tasks`      | Create a task                         |
| PUT    | `/api/tasks/{id}` | Update a task (title, done, due_date) |
| DELETE | `/api/tasks/{id}` | Delete a task                         |

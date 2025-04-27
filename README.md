# Todo App Plus MCP

A Todo application with a FastAPI backend and a Flask UI frontend.

## Project Structure

- `todo_api/` - FastAPI backend
- `todo_ui/` - Flask UI frontend
- `start_app.sh` - Bootstrap script to start both services

## Project Setup

This is an educational application that uses `uv` for dependency management with all dependencies consolidated in pyproject.toml.

1. Install all dependencies using uv:
   ```
   # Install dependencies from pyproject.toml in development mode
   uv pip install -e .
   ```

## Quick Start

The easiest way to run both the API and UI is with the bootstrap script:

```
# Start both API and UI servers
./start_app.sh
```

This script:
- Checks if servers are already running on ports 8000 and 5000
- Stops them if necessary
- Starts the API server first, then the UI server
- Provides information about where to access the application
- Can be terminated with Ctrl+C to stop both servers

## Todo API (Backend)

A simple Todo API built with FastAPI.

### Running the API Server Manually

```
# Use uv run to execute uvicorn in the virtual environment
uv run uvicorn todo_api.main:app --reload --port 8000
```

### API Endpoints

- `GET /todos`: Get all todos
- `GET /todos/{todo_id}`: Get a specific todo
- `POST /todos`: Create a new todo
- `PUT /todos/{todo_id}`: Update a todo
- `DELETE /todos/{todo_id}`: Delete a todo

### API Documentation

Once the API server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Todo UI (Frontend)

A Flask-based web interface for interacting with the Todo API.

### Running the Flask UI Server Manually

```
cd todo_ui
# Use uv run to execute python in the virtual environment
uv run python app.py
```

### Accessing the UI

After starting both servers, you can access the Todo UI at:
- http://localhost:5000

Note: Make sure the API server is running before starting the UI server, as the UI depends on the API to function properly.
"""
Main FastAPI application for the Todo API.
"""

from fastapi import FastAPI, HTTPException, Path, Depends
from typing import List, Optional

from todo_api import json_db as db
from todo_api.models import TodoCreate, TodoUpdate, TodoResponse

# Create FastAPI app
app = FastAPI(
    title="Todo API",
    description="A simple API for managing todo items",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Todo API! Go to /docs to see the API documentation."}


@app.get("/todos", response_model=List[TodoResponse])
async def get_todos():
    """Get all todos."""
    return db.get_all_todos()


@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo_data: TodoCreate):
    """Create a new todo."""
    return db.create_todo(
        title=todo_data.title,
        description=todo_data.description or "",
        completed=todo_data.completed,
        due_date=todo_data.due_date.isoformat() if todo_data.due_date else None,
    )


@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str = Path(..., description="The ID of the todo to retrieve")):
    """Get a specific todo by ID."""
    todo = db.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_data: TodoUpdate,
    todo_id: str = Path(..., description="The ID of the todo to update"),
):
    """Update an existing todo."""
    update_data = todo_data.model_dump(exclude_unset=True)

    # Convert datetime to ISO format string if present
    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = update_data["due_date"].isoformat()

    todo = db.update_todo(todo_id, update_data)
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: str = Path(..., description="The ID of the todo to delete")):
    """Delete a todo."""
    success = db.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
    return None


# Add some sample data if running in development
@app.on_event("startup")
async def startup_event():
    """Add sample data on startup."""
    if not db.get_all_todos():
        db.create_todo(
            title="Learn FastAPI",
            description="Learn how to build APIs with FastAPI",
            completed=True,
        )
        db.create_todo(
            title="Build Todo App",
            description="Create a simple todo application with FastAPI",
            completed=False,
        )

"""
Main FastAPI application for the Todo API.

This module implements a RESTful API for the Todo application using FastAPI.
It demonstrates:
1. How to create a simple CRUD API with FastAPI
2. How to use Pydantic models for request/response validation
3. How to implement proper HTTP status codes and error handling
4. How to document API endpoints with docstrings for OpenAPI/Swagger UI
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
    """
    Root endpoint that provides a welcome message.
    
    This is a simple endpoint that returns a welcome message and directs
    users to the Swagger documentation.
    
    Returns:
        dict: A message dictionary with a welcome string
    """
    return {"message": "Welcome to the Todo API! Go to /docs to see the API documentation."}


@app.get("/todos", response_model=List[TodoResponse])
async def get_todos():
    """
    Get all todo items.
    
    This endpoint retrieves a list of all todo items in the system.
    The response is validated against the TodoResponse model.
    
    Returns:
        List[TodoResponse]: A list of todo items
    """
    return db.get_all_todos()


@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo_data: TodoCreate):
    """
    Create a new todo item.
    
    This endpoint creates a new todo item using the provided data.
    Note that we return a 201 Created status code on success.
    
    Args:
        todo_data (TodoCreate): The todo data validated by Pydantic
    
    Returns:
        TodoResponse: The created todo item with generated ID and timestamps
    """
    return db.create_todo(
        title=todo_data.title,
        description=todo_data.description or "",
        completed=todo_data.completed,
        due_date=todo_data.due_date.isoformat() if todo_data.due_date else None,
    )


@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str = Path(..., description="The ID of the todo to retrieve")):
    """
    Get a specific todo by ID.
    
    This endpoint retrieves a single todo item by its unique identifier.
    It demonstrates path parameters with validation and error handling.
    
    Args:
        todo_id (str): The unique identifier of the todo to retrieve
    
    Returns:
        TodoResponse: The requested todo item
        
    Raises:
        HTTPException: 404 error if the todo is not found
    """
    todo = db.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_data: TodoUpdate,
    todo_id: str = Path(..., description="The ID of the todo to update"),
):
    """
    Update an existing todo.
    
    This endpoint updates a todo item with the provided data.
    It demonstrates:
    1. Combining path and body parameters
    2. Using Pydantic for partial updates with optional fields
    3. Proper error handling for non-existent resources
    
    Args:
        todo_data (TodoUpdate): The update data with optional fields
        todo_id (str): The ID of the todo to update
    
    Returns:
        TodoResponse: The updated todo item
        
    Raises:
        HTTPException: 404 error if the todo is not found
    """
    # Convert Pydantic model to dict, excluding unset fields for partial updates
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
    """
    Delete a todo.
    
    This endpoint deletes a todo item by its ID.
    Note that we return a 204 No Content status code on success,
    which is the appropriate status code for successful DELETE operations.
    
    Args:
        todo_id (str): The ID of the todo to delete
        
    Returns:
        None: Returns nothing on success (204 status code)
        
    Raises:
        HTTPException: 404 error if the todo is not found
    """
    success = db.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
    return None


# Add some sample data if running in development
@app.on_event("startup")
async def startup_event():
    """
    Add sample data on startup.
    
    This function is executed when the application starts.
    It checks if the database is empty and adds some sample data if needed.
    This is useful for development and demo purposes.
    
    The @app.on_event decorator is used to execute code at specific
    points in the application lifecycle.
    """
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

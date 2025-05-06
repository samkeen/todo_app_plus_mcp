"""
Todo MCP Server

A simplified server implementation using FastMCP 2.0 to expose Todo operations 
as Model Context Protocol (MCP) tools.
"""

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Import the database module
from todo_api import json_db as db

# Create the FastMCP server
mcp = FastMCP("Todo MCP")


# Define Pydantic models for tool parameters
class TodoCreate(BaseModel):
    """Model for creating todo items."""

    title: str = Field(..., description="Title of the todo item")
    description: str = Field("", description="Detailed description of the todo item")
    completed: bool = Field(False, description="Whether the todo is completed")
    due_date: Optional[str] = Field(None, description="Optional due date (ISO format)")


class TodoUpdate(BaseModel):
    """Model for updating todo items."""

    title: Optional[str] = Field(None, description="New title for the todo item")
    description: Optional[str] = Field(None, description="New description for the todo item")
    completed: Optional[bool] = Field(None, description="New completion status")
    due_date: Optional[str] = Field(None, description="New due date (ISO format)")


# Define MCP tools
@mcp.tool()
async def list_todos() -> List[Dict]:
    """List all todos in the system."""
    return db.get_all_todos()


@mcp.tool()
async def get_todo(todo_id: str) -> Optional[Dict]:
    """Get a specific todo by its ID."""
    return db.get_todo(todo_id)


@mcp.tool()
async def create_todo(todo: TodoCreate) -> Dict:
    """Create a new todo item."""
    return db.create_todo(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        due_date=todo.due_date,
    )


@mcp.tool()
async def update_todo(todo_id: str, changes: TodoUpdate) -> Optional[Dict]:
    """Update an existing todo item."""
    # Convert Pydantic model to dict, excluding None values
    update_data = {k: v for k, v in changes.model_dump().items() if v is not None}
    return db.update_todo(todo_id, update_data)


@mcp.tool()
async def delete_todo(todo_id: str) -> bool:
    """Delete a todo by ID."""
    return db.delete_todo(todo_id)


@mcp.tool()
async def get_todo_stats() -> Dict:
    """Get statistics about todos in the system."""
    todos = db.get_all_todos()
    total = len(todos)
    completed_count = sum(1 for todo in todos if todo.get("completed", False))
    completion_percentage = (completed_count / total * 100) if total > 0 else 0

    return {
        "total_count": total,
        "completed_count": completed_count,
        "incomplete_count": total - completed_count,
        "completion_percentage": round(completion_percentage, 2),
        "has_todos": total > 0,
    }


# Run the server when executed directly
if __name__ == "__main__":
    mcp.run()  # Default: runs on stdio transport

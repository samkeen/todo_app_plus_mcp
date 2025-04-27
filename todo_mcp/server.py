"""
Todo MCP Server

This module implements a Model Context Protocol (MCP) server for the Todo API
using the FastMCP framework.
"""

from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import asyncio
import json
import sys

# Import the Todo API database functions
sys.path.append("/Users/sam/Projects/todo_app_plus_mcp")
from todo_api import json_db as db
from todo_api.models import TodoBase, TodoCreate, TodoUpdate, TodoResponse

# Create the FastMCP app
mcp = FastMCP("Todo MCP Server")


# Define Pydantic models for MCP tools
class TodoData(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Title of the todo item")
    description: Optional[str] = Field(
        default="", max_length=500, description="Detailed description of the todo item"
    )
    completed: bool = Field(default=False, description="Whether the todo is completed")


class TodoUpdateData(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    completed: Optional[bool] = None


# Define MCP Tools


@mcp.tool()
async def list_todos(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all todos in the system.

    Returns:
        A list of all todo items with their details.
    """
    todos = db.get_all_todos()
    return todos


@mcp.tool()
async def get_todo(todo_id: str, ctx: Context) -> Optional[Dict[str, Any]]:
    """
    Get a specific todo by its ID.

    Args:
        todo_id: The unique identifier of the todo item.

    Returns:
        The todo item details if found, or null if not found.
    """
    todo = db.get_todo(todo_id)
    return todo


@mcp.tool()
async def create_todo(todo: TodoData, ctx: Context) -> Dict[str, Any]:
    """
    Create a new todo item.

    Args:
        todo: The todo item details to create.

    Returns:
        The created todo item with its assigned ID.
    """
    created_todo = db.create_todo(
        title=todo.title, description=todo.description or "", completed=todo.completed
    )
    return created_todo


@mcp.tool()
async def update_todo(
    todo_id: str, changes: TodoUpdateData, ctx: Context
) -> Optional[Dict[str, Any]]:
    """
    Update an existing todo item.

    Args:
        todo_id: The unique identifier of the todo to update.
        changes: The fields to update on the todo item.

    Returns:
        The updated todo item if found, or null if not found.
    """
    todo = db.update_todo(todo_id, changes.dict(exclude_unset=True))
    return todo


@mcp.tool()
async def delete_todo(todo_id: str, ctx: Context) -> bool:
    """
    Delete a todo item by its ID.

    Args:
        todo_id: The unique identifier of the todo to delete.

    Returns:
        True if the todo was deleted, False if not found.
    """
    success = db.delete_todo(todo_id)
    return success


@mcp.tool()
async def get_todo_stats(ctx: Context) -> Dict[str, Any]:
    """
    Get statistics about todos in the system.

    Returns:
        Statistics including total count, completed count, and completion percentage.
    """
    todos = db.get_all_todos()
    total = len(todos)
    completed = sum(1 for todo in todos if todo["completed"])

    return {
        "total_todos": total,
        "completed_todos": completed,
        "completion_percentage": (completed / total * 100) if total > 0 else 0,
        "has_todos": total > 0,
    }


# Add prompt capability
@mcp.prompt()
async def todo_analysis(ctx: Context, todos: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Analyze the current state of todos and provide insights.

    Args:
        todos: Optional list of todos to analyze. If not provided, all todos will be used.

    Returns:
        A detailed analysis of the todo items.
    """
    if todos is None:
        todos = db.get_all_todos()

    total = len(todos)
    completed = sum(1 for todo in todos if todo["completed"])
    completion_percentage = (completed / total * 100) if total > 0 else 0

    prompt = f"""
    # Todo Analysis
    
    ## Statistics
    - Total todos: {total}
    - Completed todos: {completed}
    - Completion percentage: {completion_percentage:.1f}%
    
    ## Todo Items
    
    """

    for todo in todos:
        status = "✅" if todo["completed"] else "⬜️"
        prompt += f"- {status} **{todo['title']}**: {todo['description']}\n"

    return prompt


# Run the server
if __name__ == "__main__":
    mcp.run()

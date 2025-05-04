"""
Todo MCP Server

This module implements a Model Context Protocol (MCP) server for the Todo API
using the FastMCP framework. It exposes Todo operations as MCP tools that can be
used by AI assistants like Claude.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

# Ensure the parent directory is in the Python path for proper imports
# This approach is more portable than hardcoding absolute paths
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Import the Todo API database functions
from todo_api import json_db as db
from todo_api.models import TodoBase, TodoCreate, TodoUpdate, TodoResponse

# Create the FastMCP app
mcp = FastMCP("Todo MCP Server")


# Define Pydantic models for MCP tools
class TodoData(BaseModel):
    """Model for creating/updating todo items via MCP."""

    title: str = Field(..., min_length=1, max_length=100, description="Title of the todo item")
    description: Optional[str] = Field(
        default="", max_length=500, description="Detailed description of the todo item"
    )
    completed: bool = Field(default=False, description="Whether the todo is completed")


class TodoUpdateData(BaseModel):
    """Model for updating todo items via MCP."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="New title for the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="New description for the todo item"
    )
    completed: Optional[bool] = Field(None, description="New completion status for the todo item")


# Define MCP Tools


@mcp.tool()
async def list_todos(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all todos in the system.

    Returns:
        A list of all todo items with their details.
    """
    try:
        todos = db.get_all_todos()
        return todos
    except Exception as e:
        ctx.runtime.logger.error(f"Error listing todos: {str(e)}")  # type: ignore
        return []


@mcp.tool()
async def get_todo(todo_id: str, ctx: Context) -> Optional[Dict[str, Any]]:
    """
    Get a specific todo by its ID.

    Args:
        todo_id: The unique identifier of the todo item.

    Returns:
        The todo item details if found, or null if not found.
    """
    try:
        todo = db.get_todo(todo_id)
        return todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error retrieving todo {todo_id}: {str(e)}")  # type: ignore
        return None


@mcp.tool()
async def create_todo(todo: TodoData, ctx: Context) -> Dict[str, Any]:
    """
    Create a new todo item.

    Args:
        todo: The todo item details to create.

    Returns:
        The created todo item with its assigned ID.
    """
    try:
        created_todo = db.create_todo(
            title=todo.title, description=todo.description or "", completed=todo.completed
        )
        return created_todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error creating todo: {str(e)}")  # type: ignore
        # Return a minimal error object that matches the expected structure
        return {
            "id": "error",
            "title": "Error creating todo",
            "description": str(e),
            "completed": False,
            "created_at": "",
            "updated_at": "",
        }


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
    try:
        # Convert Pydantic model to dict and exclude unset fields
        update_data = changes.dict(exclude_unset=True)
        todo = db.update_todo(todo_id, update_data)
        return todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error updating todo {todo_id}: {str(e)}")  # type: ignore
        return None


@mcp.tool()
async def delete_todo(todo_id: str, ctx: Context) -> bool:
    """
    Delete a todo item by its ID.

    Args:
        todo_id: The unique identifier of the todo to delete.

    Returns:
        True if the todo was deleted, False if not found or if an error occurred.
    """
    try:
        success = db.delete_todo(todo_id)
        return success
    except Exception as e:
        ctx.runtime.logger.error(f"Error deleting todo {todo_id}: {str(e)}")  # type: ignore
        return False


@mcp.tool()
async def get_todo_stats(ctx: Context) -> Dict[str, Any]:
    """
    Get statistics about todos in the system.

    Returns:
        Statistics including total count, completed count, completion percentage,
        and whether there are any todos in the system.
    """
    try:
        todos = db.get_all_todos()
        total = len(todos)
        completed = sum(1 for todo in todos if todo["completed"])
        completion_percentage = (completed / total * 100) if total > 0 else 0

        # Add more insightful statistics
        oldest_todo = min(todos, key=lambda x: x["created_at"]) if todos else None
        newest_todo = max(todos, key=lambda x: x["created_at"]) if todos else None
        incomplete_todos = [todo for todo in todos if not todo["completed"]]

        return {
            "total_todos": total,
            "completed_todos": completed,
            "incomplete_todos": total - completed,
            "completion_percentage": round(completion_percentage, 2),
            "has_todos": total > 0,
            "oldest_todo_id": oldest_todo["id"] if oldest_todo else None,
            "oldest_todo_title": oldest_todo["title"] if oldest_todo else None,
            "newest_todo_id": newest_todo["id"] if newest_todo else None,
            "newest_todo_title": newest_todo["title"] if newest_todo else None,
            "incomplete_todo_count": len(incomplete_todos),
        }
    except Exception as e:
        ctx.runtime.logger.error(f"Error getting todo stats: {str(e)}")  # type: ignore
        return {
            "total_todos": 0,
            "completed_todos": 0,
            "incomplete_todos": 0,
            "completion_percentage": 0,
            "has_todos": False,
            "error": str(e),
        }


# Add prompt capability
@mcp.prompt()
async def todo_analysis(ctx: Context, todos: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Analyze the current state of todos.

    Args:
        ctx: The MCP context.
        todos: Optional list of todos to analyze. If not provided, all todos will be fetched.

    Returns:
        A detailed analysis of the todo items.
    """
    try:
        if todos is None:
            todos = db.get_all_todos()

        total = len(todos)

        if total == 0:
            return """
            # Todo Analysis
            
            There are currently no todos in the system. Start by creating a new todo!
            """

        completed = sum(1 for todo in todos if todo["completed"])
        completion_percentage = (completed / total * 100) if total > 0 else 0

        # Sort todos by creation date
        sorted_todos = sorted(todos, key=lambda x: x["created_at"])
        oldest_todo = sorted_todos[0] if sorted_todos else None
        newest_todo = sorted_todos[-1] if sorted_todos else None

        # Find todos by completion status
        incomplete_todos = [todo for todo in todos if not todo["completed"]]
        completed_todos = [todo for todo in todos if todo["completed"]]

        # Create analysis prompt
        prompt = f"""
        # Todo Analysis
        
        ## Summary Statistics
        - Total todos: {total}
        - Completed todos: {completed} ({completion_percentage:.1f}%)
        - Incomplete todos: {total - completed} ({100 - completion_percentage:.1f}%)
        """

        # Only add timeline section if we have todos
        if oldest_todo and newest_todo:
            prompt += f"""
        
        ## Timeline
        - Oldest todo: "{oldest_todo['title']}" ({oldest_todo['created_at']})
        - Newest todo: "{newest_todo['title']}" ({newest_todo['created_at']})
        """

        prompt += f"""
        
        ## Status Breakdown
        
        ### Incomplete Todos ({len(incomplete_todos)})
        """

        if incomplete_todos:
            for todo in incomplete_todos[:5]:  # Show up to 5 incomplete todos
                prompt += f"- ⬜️ **{todo['title']}**: {todo['description']}\n"

            if len(incomplete_todos) > 5:
                prompt += f"- ... and {len(incomplete_todos) - 5} more incomplete todos\n"
        else:
            prompt += "- No incomplete todos! Great job! 🎉\n"

        prompt += f"""
        
        ### Completed Todos ({len(completed_todos)})
        """

        if completed_todos:
            for todo in completed_todos[:5]:  # Show up to 5 completed todos
                prompt += f"- ✅ **{todo['title']}**: {todo['description']}\n"

            if len(completed_todos) > 5:
                prompt += f"- ... and {len(completed_todos) - 5} more completed todos\n"
        else:
            prompt += "- No completed todos yet. Keep working! 💪\n"

        # Add recommendations
        prompt += """
        
        ## Recommendations
        """

        if len(incomplete_todos) > 5:
            prompt += (
                "- Consider prioritizing your incomplete todos to manage your workload better.\n"
            )

        if completion_percentage < 30:
            prompt += "- Your completion rate is low. Try breaking tasks into smaller todos that are easier to complete.\n"
        elif completion_percentage > 70:
            prompt += "- Great job on your high completion rate! Keep up the good work!\n"

        if len(incomplete_todos) == 0:
            prompt += "- All todos are complete! Time to add new goals or projects.\n"

        return prompt

    except Exception as e:
        ctx.runtime.logger.error(f"Error in todo analysis: {str(e)}")  # type: ignore
        return f"""
        # Todo Analysis Error
        
        Sorry, there was an error analyzing your todos: {str(e)}
        
        Please try again later or contact the administrator.
        """


# Run the server
if __name__ == "__main__":
    mcp.run()

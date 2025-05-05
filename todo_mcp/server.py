"""
Todo MCP Server

This module implements a Model Context Protocol (MCP) server for the Todo API
using the FastMCP framework. It exposes Todo operations as MCP tools that can be
used by AI assistants like Claude.

The Model Context Protocol (MCP) is an open protocol that standardizes how AI models 
interact with external tools and systems. This server demonstrates:
1. How to create a FastMCP server with custom tools
2. How to expose database operations as AI-callable functions
3. How to define parameter schemas using Pydantic models
4. How to handle errors and provide meaningful feedback
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from datetime import datetime

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
    """
    Model for creating/updating todo items via MCP.
    
    This Pydantic model defines the schema for todo item creation,
    including field types, constraints and descriptions that will be 
    exposed to the AI through the MCP protocol.
    """

    title: str = Field(..., min_length=1, max_length=100, description="Title of the todo item")
    description: Optional[str] = Field(
        default="", max_length=500, description="Detailed description of the todo item"
    )
    completed: bool = Field(default=False, description="Whether the todo is completed")
    due_date: Optional[str] = Field(default=None, description="Optional due date for the todo item (ISO format string)")


class TodoUpdateData(BaseModel):
    """
    Model for updating todo items via MCP.
    
    This model makes all fields optional, allowing partial updates to todo items.
    The AI can specify only the fields it wants to change.
    """

    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="New title for the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="New description for the todo item"
    )
    completed: Optional[bool] = Field(None, description="New completion status for the todo item")
    due_date: Optional[str] = Field(None, description="Optional due date for the todo item (ISO format string)")


# Define MCP Tools


@mcp.tool()
async def list_todos(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all todos in the system.
    
    This is an MCP tool that retrieves all todo items from the database.
    It demonstrates how to create a simple tool with no parameters.
    
    Args:
        ctx: The MCP context object, which provides access to runtime services
             like logging and tool metadata.
             
    Returns:
        A list of all todo items with their details.
    """
    try:
        # Fetch all todos from the database
        todos = db.get_all_todos()
        return todos
    except Exception as e:
        # Log the error using the MCP context logger
        ctx.runtime.logger.error(f"Error listing todos: {str(e)}")  # type: ignore
        return []


@mcp.tool()
async def get_todo(todo_id: str, ctx: Context) -> Optional[Dict[str, Any]]:
    """
    Get a specific todo by its ID.
    
    This tool demonstrates retrieving a single item using a string identifier.
    
    Args:
        todo_id: The unique identifier of the todo item.
        ctx: The MCP context object for logging and runtime services.
        
    Returns:
        The todo item details if found, or null if not found.
    """
    try:
        # Fetch a specific todo by ID
        todo = db.get_todo(todo_id)
        return todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error retrieving todo {todo_id}: {str(e)}")  # type: ignore
        return None


@mcp.tool()
async def create_todo(todo: TodoData, ctx: Context) -> Dict[str, Any]:
    """
    Create a new todo item.
    
    This tool demonstrates:
    1. Using a Pydantic model as a complex parameter
    2. Converting the model to appropriate database parameters
    3. Proper error handling with meaningful return values
    
    Args:
        todo: The todo item details to create, validated by the TodoData model.
        ctx: The MCP context object for logging and runtime services.
        
    Returns:
        The created todo item with its assigned ID.
    """
    try:
        # Create a new todo using the provided data
        created_todo = db.create_todo(
            title=todo.title, 
            description=todo.description or "", 
            completed=todo.completed,
            due_date=todo.due_date
        )
        return created_todo
    except Exception as e:
        # Log the error but also return a structured error response
        # This ensures the AI gets meaningful feedback it can interpret
        ctx.runtime.logger.error(f"Error creating todo: {str(e)}")  # type: ignore
        # Return a minimal error object that matches the expected structure
        return {
            "id": "error",
            "title": "Error creating todo",
            "description": str(e),
            "completed": False,
            "created_at": "",
            "updated_at": "",
            "due_date": None
        }


@mcp.tool()
async def update_todo(
    todo_id: str, changes: TodoUpdateData, ctx: Context
) -> Optional[Dict[str, Any]]:
    """
    Update an existing todo item.
    
    This tool demonstrates:
    1. Combining a simple parameter (todo_id) with a complex parameter (changes)
    2. Using a model specifically designed for updates with optional fields
    3. Returning appropriate results based on success or failure
    
    Args:
        todo_id: The unique identifier of the todo to update.
        changes: The fields to update on the todo item, validated by TodoUpdateData.
        ctx: The MCP context object for logging and runtime services.
        
    Returns:
        The updated todo item if found, or null if not found.
    """
    try:
        # Convert the Pydantic model to a dictionary, removing None values
        update_data = changes.dict(exclude_unset=True, exclude_none=True)
        
        # Update the todo with the filtered data
        updated_todo = db.update_todo(todo_id, update_data)
        return updated_todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error updating todo {todo_id}: {str(e)}")  # type: ignore
        return None


@mcp.tool()
async def delete_todo(todo_id: str, ctx: Context) -> bool:
    """
    Delete a todo item by its ID.
    
    This tool demonstrates:
    1. Using a simple string parameter
    2. Returning a boolean result to indicate success/failure
    3. Safe error handling
    
    Args:
        todo_id: The unique identifier of the todo to delete.
        ctx: The MCP context object for logging and runtime services.
        
    Returns:
        True if the todo was deleted, False if not found or if an error occurred.
    """
    try:
        # Delete the todo and return the result
        result = db.delete_todo(todo_id)
        return result
    except Exception as e:
        ctx.runtime.logger.error(f"Error deleting todo {todo_id}: {str(e)}")  # type: ignore
        return False


@mcp.tool()
async def get_todo_stats(ctx: Context) -> Dict[str, Any]:
    """
    Get statistics about todos in the system.
    
    This tool demonstrates:
    1. Computing derived data from database objects
    2. Structuring a complex response with multiple metrics
    3. Error handling for robustness
    
    Returns:
        Statistics including total count, completed count, completion percentage,
        and whether there are any todos in the system.
    """
    try:
        # Fetch all todos to compute statistics
        todos = db.get_all_todos()
        
        # Count totals and completed
        total = len(todos)
        completed = sum(1 for todo in todos if todo.get("completed", False))
        
        # Compute completion percentage, handling division by zero
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        # Return comprehensive statistics
        return {
            "total_count": total,
            "completed_count": completed,
            "incomplete_count": total - completed,
            "completion_percentage": round(completion_percentage, 2),
            "has_todos": total > 0,
        }
    except Exception as e:
        ctx.runtime.logger.error(f"Error getting todo stats: {str(e)}")  # type: ignore
        return {
            "total_count": 0,
            "completed_count": 0,
            "incomplete_count": 0,
            "completion_percentage": 0,
            "has_todos": False,
            "error": str(e),
        }


# Helper function to format dates
def format_date_only(date_str):
    """
    Format a date string to show only the date part (YYYY-MM-DD).
    
    This helper function takes an ISO format datetime string and extracts
    just the date portion for cleaner display.
    
    Args:
        date_str: An ISO format datetime string.
        
    Returns:
        A formatted date string in YYYY-MM-DD format.
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return date_str


# Add prompt capability
@mcp.tool()
async def todo_analysis(ctx: Context, todos: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Analyze the current state of todos.
    
    This tool demonstrates:
    1. Creating a rich text response (markdown) for display
    2. Advanced analysis of database records
    3. Optional parameters to support different use cases
    4. Grouping and categorizing data
    
    Args:
        ctx: The MCP context object for logging and runtime services.
        todos: Optional list of todos to analyze. If not provided, all todos will be fetched.
        
    Returns:
        A detailed analysis of the todo items formatted in markdown.
    """
    try:
        # Fetch todos if not provided
        if todos is None:
            todos = db.get_all_todos()
        
        # If no todos exist, return early with a simple message
        if not todos:
            return """
            # Todo Analysis
            
            No todos found in the system. Add some todos to get started!
            """
        
        # Group and categorize todos
        completed_todos = [todo for todo in todos if todo.get("completed", False)]
        incomplete_todos = [todo for todo in todos if not todo.get("completed", False)]
        
        # Calculate statistics
        total = len(todos)
        completed_count = len(completed_todos)
        completion_percentage = (completed_count / total * 100) if total > 0 else 0
        
        # Find oldest and newest todos based on creation date
        sorted_by_date = sorted(todos, key=lambda x: x.get("created_at", ""))
        oldest_todo = sorted_by_date[0] if sorted_by_date else None
        newest_todo = sorted_by_date[-1] if sorted_by_date else None
        
        # Count todos with due dates, and count overdue todos
        todos_with_due_dates = [todo for todo in todos if todo.get("due_date")]
        overdue_todos = []
        upcoming_todos = []
        
        now = datetime.now()
        
        for todo in todos_with_due_dates:
            if not todo["completed"] and todo.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(todo["due_date"].replace("Z", "+00:00"))
                    if due_date < now:
                        overdue_todos.append(todo)
                    else:
                        upcoming_todos.append(todo)
                except (ValueError, TypeError):
                    # Skip todos with invalid date format
                    pass
        
        # Create analysis prompt
        prompt = f"""
        # Todo Analysis
        
        ## Summary Statistics
        - Total todos: {total}
        - Completed todos: {completed_count} ({completion_percentage:.1f}%)
        - Incomplete todos: {total - completed_count} ({100 - completion_percentage:.1f}%)
        """
        
        # Add due date statistics if relevant
        if overdue_todos or upcoming_todos:
            prompt += f"""
        - Overdue todos: {len(overdue_todos)}
        - Upcoming todos: {len(upcoming_todos)}
        """

        # Only add timeline section if we have todos
        if oldest_todo and newest_todo:
            prompt += f"""
        
        ## Timeline
        - Oldest todo: "{oldest_todo['title']}" (Created: {format_date_only(oldest_todo['created_at'])})
        - Newest todo: "{newest_todo['title']}" (Created: {format_date_only(newest_todo['created_at'])})
        """

        prompt += f"""
        
        ## Status Breakdown
        
        ### Incomplete Todos ({len(incomplete_todos)})
        """

        if incomplete_todos:
            for todo in incomplete_todos[:5]:  # Show up to 5 incomplete todos
                due_date_str = ""
                if todo.get("due_date"):
                    try:
                        due_date_str = f" (Due: {format_date_only(todo['due_date'])})"
                    except (ValueError, TypeError):
                        pass
                prompt += f"- ⬜️ **{todo['title']}**{due_date_str}: {todo['description']}\n"

            if len(incomplete_todos) > 5:
                prompt += f"- ... and {len(incomplete_todos) - 5} more incomplete todos\n"
        else:
            prompt += "- No incomplete todos! Great job! 🎉\n"
            
        # Add overdue section if there are overdue todos
        if overdue_todos:
            prompt += f"""
        
        ### Overdue Todos ({len(overdue_todos)})
        """
            for todo in overdue_todos[:3]:  # Show up to 3 overdue todos
                try:
                    due_date_str = f" (Due: {format_date_only(todo['due_date'])})"
                except (ValueError, TypeError):
                    due_date_str = ""
                prompt += f"- 🚨 **{todo['title']}**{due_date_str}: {todo['description']}\n"
            
            if len(overdue_todos) > 3:
                prompt += f"- ... and {len(overdue_todos) - 3} more overdue todos\n"

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
            
        if len(overdue_todos) > 0:
            prompt += "- You have overdue tasks. Consider addressing these first or rescheduling them if needed.\n"

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

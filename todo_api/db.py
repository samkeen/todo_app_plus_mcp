"""
Database module for the todo app.
In a real application, you would use a proper database like SQLite or PostgreSQL.
For simplicity, we're using an in-memory store.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid

# In-memory store for todos
todos_db: Dict[str, dict] = {}

def get_all_todos() -> List[dict]:
    """Return all todos."""
    return list(todos_db.values())

def get_todo(todo_id: str) -> Optional[dict]:
    """Get a specific todo by ID."""
    return todos_db.get(todo_id)

def create_todo(title: str, description: str = "", completed: bool = False) -> dict:
    """Create a new todo."""
    todo_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    todo = {
        "id": todo_id,
        "title": title,
        "description": description,
        "completed": completed,
        "created_at": created_at,
        "updated_at": created_at
    }
    todos_db[todo_id] = todo
    return todo

def update_todo(todo_id: str, data: dict) -> Optional[dict]:
    """Update an existing todo."""
    if todo_id not in todos_db:
        return None
    
    todo = todos_db[todo_id]
    
    # Update fields
    if "title" in data:
        todo["title"] = data["title"]
    if "description" in data:
        todo["description"] = data["description"]
    if "completed" in data:
        todo["completed"] = data["completed"]
    
    # Update the 'updated_at' timestamp
    todo["updated_at"] = datetime.now().isoformat()
    
    return todo

def delete_todo(todo_id: str) -> bool:
    """Delete a todo by ID."""
    if todo_id not in todos_db:
        return False
    
    del todos_db[todo_id]
    return True

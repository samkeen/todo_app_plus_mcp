"""
JSON file-based database module for the todo app.
This module provides a simple file-based storage for todos using JSON.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import uuid
import threading

# Path to the JSON database file
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "todo_data.json")

# Lock for thread safety when accessing the file
file_lock = threading.Lock()

def _load_todos() -> Dict[str, dict]:
    """Load todos from the JSON file."""
    if not os.path.exists(DB_FILE):
        return {}
    
    with file_lock:
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

def _save_todos(todos: Dict[str, dict]) -> None:
    """Save todos to the JSON file."""
    with file_lock:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        with open(DB_FILE, 'w') as f:
            json.dump(todos, f, indent=2)

def get_all_todos() -> List[dict]:
    """Return all todos."""
    todos_db = _load_todos()
    return list(todos_db.values())

def get_todo(todo_id: str) -> Optional[dict]:
    """Get a specific todo by ID."""
    todos_db = _load_todos()
    return todos_db.get(todo_id)

def create_todo(title: str, description: str = "", completed: bool = False) -> dict:
    """Create a new todo."""
    todos_db = _load_todos()
    
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
    
    _save_todos(todos_db)
    return todo

def update_todo(todo_id: str, data: dict) -> Optional[dict]:
    """Update an existing todo."""
    todos_db = _load_todos()
    
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
    
    _save_todos(todos_db)
    return todo

def delete_todo(todo_id: str) -> bool:
    """Delete a todo by ID."""
    todos_db = _load_todos()
    
    if todo_id not in todos_db:
        return False
    
    del todos_db[todo_id]
    _save_todos(todos_db)
    return True

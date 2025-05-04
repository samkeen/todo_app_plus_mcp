"""
JSON file-based database module for the todo app.
This module provides a simple file-based storage for todos using JSON.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import uuid
import threading
import shutil

# Path to the JSON database files
BASE_DIR = Path(__file__).parent.parent
DB_FILE = BASE_DIR / "todo_data.json"
SAMPLE_DB_FILE = BASE_DIR / "todo_data.sample.json"

# Lock for thread safety when accessing the file
file_lock = threading.Lock()

def _load_todos() -> Dict[str, dict]:
    """
    Load todos from the JSON file.
    
    If todo_data.json doesn't exist, attempts to load from todo_data.sample.json
    and creates todo_data.json from it.
    """
    with file_lock:
        # Check if the primary database file exists
        if not DB_FILE.exists():
            # If the sample file exists, use it as a template
            if SAMPLE_DB_FILE.exists():
                try:
                    with SAMPLE_DB_FILE.open('r') as sample_file:
                        todos = json.load(sample_file)
                    
                    # Create the data file from the sample
                    with DB_FILE.open('w') as data_file:
                        json.dump(todos, data_file, indent=2)
                    
                    return todos
                except (json.JSONDecodeError, FileNotFoundError):
                    # If sample file has issues, create an empty database
                    empty_db = {}
                    with DB_FILE.open('w') as f:
                        json.dump(empty_db, f, indent=2)
                    return empty_db
            else:
                # Neither file exists, create an empty database
                empty_db = {}
                DB_FILE.parent.mkdir(parents=True, exist_ok=True)
                with DB_FILE.open('w') as f:
                    json.dump(empty_db, f, indent=2)
                return empty_db
        
        # Normal case: load from the existing data file
        try:
            with DB_FILE.open('r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Handle corrupted JSON file
            empty_db = {}
            with DB_FILE.open('w') as f:
                json.dump(empty_db, f, indent=2)
            return empty_db

def _save_todos(todos: Dict[str, dict]) -> None:
    """Save todos to the JSON file."""
    with file_lock:
        # Create directory if it doesn't exist
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with DB_FILE.open('w') as f:
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

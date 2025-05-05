"""
Pydantic models for the todo app.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TodoBase(BaseModel):
    """Base model for todo items."""
    title: str = Field(..., min_length=1, max_length=100, description="Title of the todo item")
    description: Optional[str] = Field(
        default="", max_length=500, description="Detailed description of the todo item"
    )
    completed: bool = Field(default=False, description="Whether the todo is completed")
    due_date: Optional[datetime] = Field(default=None, description="Optional due date for the todo item")


class TodoCreate(TodoBase):
    """Model for creating a new todo."""
    pass


class TodoUpdate(BaseModel):
    """Model for updating an existing todo."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class TodoResponse(TodoBase):
    """Model for todo response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuration for the Pydantic model."""
        from_attributes = True

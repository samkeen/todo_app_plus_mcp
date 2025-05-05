# Understanding the Model Context Protocol (MCP)

This document explains the Model Context Protocol (MCP) implementation in the Todo App Plus project, providing a clear guide for those new to MCP.

## What is the Model Context Protocol (MCP)?

The Model Context Protocol (MCP) is a standardized way for AI assistants (like Claude) to interact with external systems, tools, and data sources. It allows AI models to:

1. **Discover available tools** that they can use to perform actions
2. **Call these tools** to retrieve information or make changes
3. **Access prompts** to generate specialized content

Think of MCP as an API designed specifically for AI assistants. While traditional APIs are designed for developers to use in code, MCP is designed to be used directly by AI models.

## Why Use MCP?

MCP offers several advantages:

1. **AI-Native Interface**: Tools are described in a way that AI models can understand and use effectively
2. **Structured Interactions**: Consistent format for tool descriptions, parameters, and responses
3. **Discoverable Capabilities**: AIs can explore what's available without hardcoding
4. **Extensibility**: New capabilities can be added without changing the AI model itself

For our Todo application, MCP allows AI assistants to directly interact with the todo database, retrieving information and making changes without requiring a human to use the web UI or make API calls.

## MCP Implementation in Todo App Plus

Our Todo App consists of four main components:

1. **FastAPI Backend** (`todo_api/`): The core API providing CRUD operations for todos
2. **Flask UI Frontend** (`todo_ui/`): A web interface for humans to interact with todos
3. **MCP Server** (`todo_mcp/`): An interface allowing AI assistants to interact with todos
4. **Chat CLI** (`todo_chat/`): A command-line chat interface for interacting with the Todo app via Claude and MCP

The MCP server acts as a bridge between AI assistants and the Todo database:

```
┌────────────┐           ┌───────────┐           ┌──────────┐
│            │  HTTP/    │           │           │          │
│ AI         ├───────────┤ MCP       ├───────────┤ Todo     │
│ Assistant  │  MCP      │ Server    │  Direct   │ Database │
│            │           │           │  Access   │          │
└────────────┘           └───────────┘           └──────────┘
```

## Todo Data Model

Each todo item in our system has the following properties:

- **Title**: Required field describing the task (1-100 characters)
- **Description**: Optional detailed description (up to 500 characters)
- **Completed**: Boolean flag indicating completion status (default: false)
- **Due Date**: Optional deadline for the todo item (ISO format date)
- **ID**: Unique identifier (automatically assigned)
- **Created At**: Timestamp of creation (automatically assigned)
- **Updated At**: Timestamp of last update (automatically assigned)

## MCP Tools in Todo App Plus

Our MCP server provides the following tools:

1. **list_todos**: Retrieves all todos in the system
2. **get_todo**: Gets a specific todo by ID
3. **create_todo**: Creates a new todo item with title, description, completion status, and optional due date
4. **update_todo**: Updates an existing todo (any field can be selectively updated)
5. **delete_todo**: Deletes a todo by ID
6. **get_todo_stats**: Provides statistics about todos (count, completion %, etc.)

Additionally, it offers a **todo_analysis** prompt to generate insights about the current state of todos, including overdue items and personalized recommendations.

## Setting Up and Running the MCP Server

### Prerequisites

- Python 3.10 or higher
- The Todo API backend must be properly set up (dependencies installed)

### Installation

The MCP server is installed as part of the Todo App Plus package. All dependencies are consolidated in the project's `pyproject.toml` file.

```bash
# Install all dependencies
uv pip install -e .
```

### Running the MCP Server

You can run the MCP server directly:

```bash
# Run the MCP server
uv run python -m todo_mcp.server
```

### Testing with MCP Inspector

The MCP CLI tool provides an interactive interface to test your MCP server:

```bash
# Start the MCP Inspector
uv run mcp dev todo_mcp/server.py
```

This will open an interactive UI where you can test the available tools and prompts.

### Using with the Todo Chat CLI

The Todo App includes a command-line chat interface for interacting with Claude AI and the Todo app through MCP:

```bash
# Set your Anthropic API key in an .env file first
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Run the Chat CLI
uv run python -m todo_chat.chat_cli
```

### Using with Claude AI

To use this MCP server with Claude:

1. Install the MCP CLI tool: `pip install mcp-cli`
2. Install the server: `mcp install todo_mcp/server.py --name "Todo MCP Server"`
3. The server will now be available as a tool for Claude in the Claude Desktop app or Claude web interface

## Example Interactions

Here are examples of how an AI assistant might use the MCP tools:

### Listing Todos

```
AI Assistant: Let me check your current todos.
[AI calls list_todos tool]
AI Assistant: You have 3 todos:
1. "Complete project report" (Not completed, Due: 2025-05-10)
2. "Schedule team meeting" (Completed)
3. "Prepare presentation slides" (Not completed, Due: 2025-05-15)
```

### Creating a Todo

```
AI Assistant: I'll add that task to your todo list.
[AI calls create_todo tool with appropriate parameters]
AI Assistant: I've added "Review proposal draft" to your todo list with a due date of May 20th.
```

### Analyzing Todos

```
AI Assistant: Let me analyze your current todos.
[AI calls todo_analysis prompt]
AI Assistant: You have 4 todos with a completion rate of 25%. 
Your oldest todo is "Complete project report" and is overdue by 2 days.
I recommend focusing on this overdue item first before starting new tasks.
```

## Technical Details

### MCP Server Implementation

The MCP server is implemented using the FastMCP framework, which builds on FastAPI. Each tool is defined as an asynchronous function with appropriate type annotations.

For example, the `create_todo` tool is implemented as:

```python
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
            title=todo.title, 
            description=todo.description or "", 
            completed=todo.completed,
            due_date=todo.due_date
        )
        return created_todo
    except Exception as e:
        ctx.runtime.logger.error(f"Error creating todo: {str(e)}")
        # Return a minimal error object
        return {
            "id": "error",
            "title": "Error creating todo",
            "description": str(e),
            "completed": False,
            "created_at": "",
            "updated_at": "",
            "due_date": None
        }
```

The `@mcp.tool()` decorator registers this function as an MCP tool, making it available to AI assistants.

### Data Models

The MCP server uses Pydantic models to define the structure of data passed to and from tools:

- `TodoData`: Used for creating new todos, including title, description, completed status, and due date
- `TodoUpdateData`: Used for updating existing todos, with all fields optional to allow partial updates

These models include validation rules to ensure data consistency and type safety.

## Extending the MCP Server

To add new capabilities to the MCP server, you can:

1. Add new tools by defining functions with the `@mcp.tool()` decorator
2. Add new prompts with the `@mcp.prompt()` decorator
3. Update existing tools to provide additional functionality

For example, to add a tool that filters todos by completion status:

```python
@mcp.tool()
async def filter_todos(completed: bool, ctx: Context) -> List[Dict[str, Any]]:
    """
    Get todos filtered by completion status.
    
    Args:
        completed: Whether to return completed (True) or incomplete (False) todos.
        
    Returns:
        List of todos matching the completion status.
    """
    try:
        todos = db.get_all_todos()
        filtered_todos = [todo for todo in todos if todo["completed"] == completed]
        return filtered_todos
    except Exception as e:
        ctx.runtime.logger.error(f"Error filtering todos: {str(e)}")
        return []
```

## Conclusion

The Model Context Protocol provides a powerful way to enable AI assistants to interact with your Todo application. By implementing an MCP server, you've created a bridge that allows AIs to help users manage their todos, provide insights, and take actions on their behalf.

This implementation serves as a foundation that can be extended with additional tools and prompts as needed.

## Further Reading

- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification/2025-03-26)
- [MCP CLI Documentation](https://modelcontextprotocol.io/cli/)
- [FastMCP Framework Documentation](https://modelcontextprotocol.io/fastmcp/)
- [MCP Server Documentation](https://modelcontextprotocol.io/server/)
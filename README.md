# Todo App Plus MCP

A Todo application with a FastAPI backend, a Flask UI frontend, and a Model Context Protocol (MCP) server.

## Project Structure

- `todo_api/` - FastAPI backend
- `todo_ui/` - Flask UI frontend
- `todo_mcp/` - Model Context Protocol server
- `start_app.sh` - Bootstrap script to start API and UI services

## Project Setup

This is an educational application that uses `uv` for dependency management with all dependencies consolidated in pyproject.toml.

1. Install all dependencies using uv:
   ```
   # Install dependencies from pyproject.toml in development mode
   uv pip install -e .
   ```

## Quick Start

The easiest way to run both the API and UI is with the bootstrap script:

```
# Start both API and UI servers
./start_app.sh
```

This script:
- Checks if servers are already running on ports 8000 and 5000
- Stops them if necessary
- Starts the API server first, then the UI server
- Provides information about where to access the application
- Can be terminated with Ctrl+C to stop both servers

## Todo API (Backend)

A simple Todo API built with FastAPI.

### Running the API Server Manually

```
# Use uv run to execute uvicorn in the virtual environment
uv run uvicorn todo_api.main:app --reload --port 8000
```

### API Endpoints

- `GET /todos`: Get all todos
- `GET /todos/{todo_id}`: Get a specific todo
- `POST /todos`: Create a new todo
- `PUT /todos/{todo_id}`: Update a todo
- `DELETE /todos/{todo_id}`: Delete a todo

### API Documentation

Once the API server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Todo UI (Frontend)

A Flask-based web interface for interacting with the Todo API.

### Running the Flask UI Server Manually

```
cd todo_ui
# Use uv run to execute python in the virtual environment
uv run python app.py
```

### Accessing the UI

After starting both servers, you can access the Todo UI at:
- http://localhost:5000

Note: Make sure the API server is running before starting the UI server, as the UI depends on the API to function properly.

## Todo MCP Server

An implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/specification/2025-03-26) server for the Todo API. This server allows AI assistants like Claude to interact with the Todo application by exposing MCP tools and prompts.

### Running the MCP Server

```bash
# First, ensure dependencies are installed
uv pip install -e .

# Run the MCP server
uv run python -m todo_mcp.server
```

### MCP Tools

The MCP server provides the following tools:

- `list_todos`: List all todos in the system
- `get_todo`: Get a specific todo by ID
- `create_todo`: Create a new todo item
- `update_todo`: Update an existing todo item
- `delete_todo`: Delete a todo item by ID
- `get_todo_stats`: Get statistics about todos in the system

### MCP Prompts

The MCP server also provides prompts for more complex analysis:

- `todo_analysis`: Analyze the current state of todos and provide insights

### Testing with the MCP Inspector

The easiest way to test your MCP server is using the built-in MCP Inspector tool:

```bash
# Install MCP CLI
pip install mcp-cli

# Start the MCP Inspector
mcp dev todo_mcp/server.py
```

Alternatively, you can run it with uv:

```bash
uv run --with mcp mcp run todo_mcp/server.py
```

The MCP Inspector provides an interactive UI where you can:
- View and test all available tools
- Call tools with custom parameters
- Explore available prompts
- See the server history and responses

### Testing with the Client Example

A client example is also included to demonstrate how to interact with the MCP server programmatically:

```bash
# Run the client example
uv run python -m todo_mcp.client_example
```

### Using with Claude AI

To use this MCP server with Claude AI:

1. Install the MCP CLI tool: `pip install mcp-cli`
2. Install the server: `mcp install todo_mcp/server.py --name "Todo MCP Server"`
3. The server will now be available as a tool for Claude in the Claude Desktop app or Claude web interface

Note: The MCP server depends on the Todo API database module, but it accesses the database directly rather than going through the API endpoints.
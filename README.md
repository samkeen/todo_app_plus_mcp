# Todo App Plus MCP

A Todo application with a FastAPI backend, a Flask UI frontend, and a Model Context Protocol (MCP) server.

## Project Structure

- `todo_api/` - FastAPI backend
- `todo_ui/` - Flask UI frontend
- `todo_mcp/` - Model Context Protocol server
- `todo_data.sample.json` - Sample data that will be used to create todo_data.json on first run

## Project Setup

This is an educational application that uses `uv` for dependency management with all dependencies consolidated in pyproject.toml.

1. Install all dependencies using uv:
   ```
   # Install dependencies from pyproject.toml in development mode
   uv pip install -e .
   ```

## Running the Application

The application consists of two main components that need to be running simultaneously:
1. The Todo API (Backend) - Serves data via REST endpoints
2. The Todo UI (Frontend) - Provides a web interface

### Running the Todo API (Backend)

The API is built with FastAPI and needs to be started first as the UI depends on it.

```bash
# Start the API server on port 8000
uv run uvicorn todo_api.main:app --reload --port 8000
```

Once running, the API will be available at:
- http://localhost:8000

The API also provides interactive documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running the Todo UI (Frontend)

After starting the API server, run the UI server in a separate terminal:

```bash
# Start the UI server on port 8001
uv run python -m todo_ui.app
```

Once running, the web interface will be available at:
- http://localhost:8001

![Todo UI](./docs/img/ui.png)

### Data Storage

The application uses a JSON file for data storage:
- On first run, the application will check for the existence of `todo_data.json`
- If `todo_data.json` doesn't exist, it will create one based on `todo_data.sample.json`
- Your personal todo data is stored in `todo_data.json` which is ignored by Git to prevent accidentally committing personal data

## API Endpoints

- `GET /todos`: Get all todos
- `GET /todos/{todo_id}`: Get a specific todo
- `POST /todos`: Create a new todo
- `PUT /todos/{todo_id}`: Update a todo
- `DELETE /todos/{todo_id}`: Delete a todo

## Todo MCP Server

An implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/specification/2025-03-26) server for the Todo API. This server allows AI assistants like Claude to interact with the Todo application by exposing MCP tools and prompts.

### Running the MCP Server

```bash
# First, ensure dependencies are installed
uv sync

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
uv add mcp-cli

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

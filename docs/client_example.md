# MCP Client Example Documentation

This document explains the purpose and usage of the Model Context Protocol (MCP) client example included in the Todo App Plus MCP project.

## Purpose

The MCP client example serves several important purposes:

1. **Demonstration of MCP Client SDK**: It shows how to use the official MCP Python SDK client to connect to and communicate with an MCP server.

2. **Educational Resource**: It serves as a reference implementation for developers wanting to build their own clients that interact with the Todo MCP server.

3. **Testing Tool**: It provides a way to test the MCP server functionality without using the MCP Inspector UI or integrating with Claude.

4. **Code Sample**: It demonstrates the proper patterns for asynchronous communication with MCP servers.

## How It Works

The client example establishes a connection to the MCP server and demonstrates various interactions:

1. **Establishes a Connection**: Uses `StdioServerParameters` and `stdio_client` to set up a connection to the MCP server through standard input/output streams.

2. **Creates a Session**: Initializes a session with the MCP server, which is the primary interface for all interactions.

3. **Discovers Capabilities**: Lists available tools and prompts from the server, showing developers how to discover what functionality is available.

4. **Demonstrates Tool Calls**: Makes example calls to various tools like `list_todos`, `create_todo`, and `get_todo_stats`, showing how to pass parameters and handle responses.

5. **Shows Prompt Usage**: Retrieves and displays the `todo_analysis` prompt, demonstrating how to use the prompt functionality.

## Usage Examples

### Running the Client Example

To run the client example:

```bash
# Install dependencies if you haven't already
uv pip install -e .

# Run the client example
uv run python -m todo_mcp.client_example
```

### Basic MCP Client Connection

```python
import asyncio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def connect_to_mcp_server():
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",  # Executable
        args=["-m", "todo_mcp.server"],  # Module to run
    )
    
    # Establish connection and create session
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Session is now ready for interaction
            return session

# Run the connection example
asyncio.run(connect_to_mcp_server())
```

### Discovering Available Tools

```python
async def discover_tools(session):
    # Get all available tools
    tools = await session.list_tools()
    
    # Display tool information
    for tool in tools:
        if hasattr(tool, 'name') and hasattr(tool, 'description'):
            print(f"- {tool.name}: {tool.description}")
        elif isinstance(tool, tuple) and len(tool) >= 2:
            print(f"- {tool[0]}: {tool[1]}")
        else:
            print(f"- {tool}")
```

### Calling a Tool

```python
async def list_all_todos(session):
    # Call the list_todos tool with no parameters
    todos = await session.call_tool("list_todos", {})
    
    # Process and display results
    for todo in todos:
        status = "✓" if todo["completed"] else "□"
        print(f"{status} {todo['title']}: {todo['description']}")

async def create_new_todo(session, title, description="", completed=False):
    # Call the create_todo tool with parameters
    new_todo = await session.call_tool("create_todo", {
        "todo": {
            "title": title,
            "description": description,
            "completed": completed
        }
    })
    
    print(f"Created new todo with ID: {new_todo['id']}")
    return new_todo
```

### Using a Prompt

```python
async def analyze_todos(session):
    # Get the todo_analysis prompt
    analysis = await session.get_prompt("todo_analysis", {})
    
    # Display the analysis
    print(analysis)
```

## Integration Examples

### Command-Line Todo Manager

```python
import asyncio
import argparse
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    parser = argparse.ArgumentParser(description="Todo CLI Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add list command
    subparsers.add_parser("list", help="List all todos")
    
    # Add create command
    create_parser = subparsers.add_parser("create", help="Create a new todo")
    create_parser.add_argument("title", help="Todo title")
    create_parser.add_argument("--description", "-d", default="", help="Todo description")
    create_parser.add_argument("--completed", "-c", action="store_true", help="Mark as completed")
    
    args = parser.parse_args()
    
    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "todo_mcp.server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            if args.command == "list":
                todos = await session.call_tool("list_todos", {})
                for todo in todos:
                    status = "✓" if todo["completed"] else "□"
                    print(f"{status} {todo['title']}: {todo['description']}")
                    
            elif args.command == "create":
                new_todo = await session.call_tool("create_todo", {
                    "todo": {
                        "title": args.title,
                        "description": args.description,
                        "completed": args.completed
                    }
                })
                print(f"Created todo: {new_todo['title']} (ID: {new_todo['id']})")

if __name__ == "__main__":
    asyncio.run(main())
```

### Integration with a Web Application

```python
from flask import Flask, jsonify, request
import asyncio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

app = Flask(__name__)

# Helper function to get MCP session
async def get_mcp_session():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "todo_mcp.server"],
    )
    
    read, write = await stdio_client(server_params).__aenter__()
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    
    return session, read, write

# Helper to run async functions
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/todos", methods=["GET"])
def get_todos():
    async def fetch_todos():
        session, read, write = await get_mcp_session()
        try:
            return await session.call_tool("list_todos", {})
        finally:
            await session.__aexit__(None, None, None)
            await stdio_client(None).__aexit__(None, None, None)
    
    todos = run_async(fetch_todos())
    return jsonify(todos)

@app.route("/todos", methods=["POST"])
def create_todo():
    data = request.json
    
    async def create_new_todo():
        session, read, write = await get_mcp_session()
        try:
            return await session.call_tool("create_todo", {
                "todo": {
                    "title": data["title"],
                    "description": data.get("description", ""),
                    "completed": data.get("completed", False)
                }
            })
        finally:
            await session.__aexit__(None, None, None)
            await stdio_client(None).__aexit__(None, None, None)
    
    new_todo = run_async(create_new_todo())
    return jsonify(new_todo), 201
```

## Extending the Client Example

The client example can be extended in various ways to suit different needs:

1. **Error Handling**: Add more robust error handling for network issues and server errors.

2. **Connection Pooling**: Implement connection pooling to reuse MCP sessions for better performance.

3. **Authentication**: Add authentication mechanisms if your MCP server requires it.

4. **Batch Operations**: Implement batch operations for processing multiple todos at once.

5. **Real-time Updates**: Integrate with websockets or SSE for real-time updates from the MCP server.

## Conclusion

The MCP client example serves as a foundation for building applications that leverage the Todo MCP server. By understanding and extending this example, developers can create sophisticated applications that interact with the MCP server in various ways, from simple command-line tools to complex web applications.

The flexibility of the MCP protocol allows for a wide range of integration possibilities, making it a powerful tool for AI-enabled applications that need to interact with your todo data.

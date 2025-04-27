"""
Example client for the Todo MCP server.

This demonstrates how to connect to the Todo MCP server and use its tools.
"""

import asyncio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import json


async def main():
    """Run the client example."""
    print("Connecting to Todo MCP server...")
    
    # Connect to the server using stdio
    server_params = StdioServerParameters(
        command="python",  # Executable
        args=["-m", "todo_mcp.server"],  # Module to run
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("\n=== AVAILABLE TOOLS ===")
            tools = await session.list_tools()
            for tool in tools:
                # Tool structure might vary depending on MCP version
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    print(f"- {tool.name}: {tool.description}")
                elif isinstance(tool, tuple) and len(tool) >= 2:
                    print(f"- {tool[0]}: {tool[1]}")
                else:
                    print(f"- {tool}")
            
            print("\n=== AVAILABLE PROMPTS ===")
            prompts = await session.list_prompts()
            for prompt in prompts:
                # Prompt structure might vary depending on MCP version
                if hasattr(prompt, 'name') and hasattr(prompt, 'description'):
                    print(f"- {prompt.name}: {prompt.description}")
                elif isinstance(prompt, tuple) and len(prompt) >= 2:
                    print(f"- {prompt[0]}: {prompt[1]}")
                else:
                    print(f"- {prompt}")
            
            # Example 1: List all todos
            print("\n=== LISTING ALL TODOS ===")
            todos_result = await session.call_tool("list_todos", {})
            print(json.dumps(todos_result, indent=2))
            
            # Example 2: Create a new todo
            print("\n=== CREATING A NEW TODO ===")
            new_todo = await session.call_tool("create_todo", {
                "todo": {
                    "title": "Try out MCP",
                    "description": "Learn how to use the Model Context Protocol",
                    "completed": False
                }
            })
            print(json.dumps(new_todo, indent=2))
            
            # Example 3: Get todo stats
            print("\n=== TODO STATISTICS ===")
            stats = await session.call_tool("get_todo_stats", {})
            print(json.dumps(stats, indent=2))
            
            # Example 4: Use the todo_analysis prompt
            print("\n=== TODO ANALYSIS ===")
            analysis = await session.get_prompt("todo_analysis", {})
            print(analysis)


if __name__ == "__main__":
    asyncio.run(main())

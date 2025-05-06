"""
Todo Chat CLI

A simplified chat interface using FastMCP's Client and Anthropic's SDK.
"""

import os
import asyncio
import json
from datetime import datetime
import typer
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.spinner import Spinner
from rich.live import Live
from dotenv import load_dotenv
from fastmcp import Client
from anthropic import AsyncAnthropic
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Check for API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not found. Set it in .env file.")
    exit(1)

# Configuration
MODEL = os.getenv("MODEL") or "claude-3-5-haiku-latest"

# Set up console for pretty output
custom_theme = Theme(
    {
        "user": "bold blue",
        "assistant": "bold green",
        "system": "bold yellow",
        "error": "bold red",
        "tool": "bold cyan",
    }
)
console = Console(theme=custom_theme)

# Create Typer app
app = typer.Typer(help="Chat with Claude AI and manage todos")

# Global variables for visual feedback
spinner_live: Optional[Live] = None


def start_spinner(message: str = "Thinking") -> None:
    """Start a spinner animation for visual feedback."""
    global spinner_live
    spinner = Spinner("dots", text=f"[spinner_text]{message}...[/]")
    spinner_live = Live(spinner, console=console, refresh_per_second=10)
    spinner_live.start()


def stop_spinner() -> None:
    """Stop the spinner animation."""
    global spinner_live
    if spinner_live:
        spinner_live.stop()
        spinner_live = None


def make_json_serializable(obj):
    """Convert an object to a JSON serializable format."""
    if hasattr(obj, "text"):
        return obj.text
    elif hasattr(obj, "__dict__"):
        return {
            k: make_json_serializable(v) for k, v in obj.__dict__.items() if not k.startswith("_")
        }
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    else:
        return str(obj)


async def chat_loop():
    """Main chat loop with Claude and MCP."""
    console.print(
        Panel.fit(
            "Todo Chat CLI",
            title="Welcome",
            subtitle="Type 'exit' or 'quit' to end the conversation",
        )
    )

    # System message for Claude
    system_message = f"""You are Todo Assistant, an AI that helps users manage their todo list through natural language.
Your primary function is to create and manage todo items by intelligently converting user statements into todo items.
Today's date is {datetime.now().strftime("%Y-%m-%d")}

Key behaviors:
- When a user mentions a task or action they need to do, assume they want to create a todo item for it.
- If the user implies a due date for the task, calculate the due date relative to today.
- Extract relevant details from user input to create todo items with descriptive titles and useful descriptions.
- Use the provided tools to interact with the todo list.
- Be helpful, friendly, and concise in your responses.
"""

    # Welcome message
    console.print(
        Panel(
            "[assistant]Hello! I'm your Todo Assistant. I can help you manage your todo list through natural language. What would you like to do with your todos today?[/]",
            border_style="green",
        )
    )

    try:
        # Initialize Anthropic client
        anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        # Initialize message history
        messages = []

        console.print("[system]Connecting to MCP server...[/]")

        # Connect to the MCP server using a relative file path rather than module path
        client = Client("todo_mcp/server.py")

        # Use async context manager to handle connection lifecycle
        async with client:
            # List available tools
            tools = await client.list_tools()
            console.print(f"[system]Connected to MCP server with {len(tools)} tools[/]")

            # Format tools for Anthropic
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )

            # Main chat loop
            while True:
                # Get user input
                user_input = typer.prompt("[user]You[/]")

                # Check for exit command
                if user_input.lower() in ["exit", "quit", "bye"]:
                    console.print("[assistant]Todo Assistant: Goodbye! Have a great day![/]")
                    break

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                # Show thinking indicator
                start_spinner()

                try:
                    # Send message to Claude with MCP tools
                    response = await anthropic.messages.create(
                        model=MODEL,
                        max_tokens=4096,
                        system=system_message,
                        messages=messages,
                        tools=anthropic_tools,
                    )

                    # Stop spinner after receiving response
                    stop_spinner()

                    # Process the response
                    need_follow_up = False
                    follow_up_messages = messages.copy()

                    for content_block in response.content:
                        if content_block.type == "text":
                            # Regular text response
                            console.print(
                                Panel(f"[assistant]{content_block.text}[/]", border_style="green")
                            )

                            # Add to message history
                            messages.append({"role": "assistant", "content": content_block.text})

                        elif content_block.type == "tool_use":
                            # Tool call
                            need_follow_up = True
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_id = content_block.id

                            # Log the tool call
                            console.print(f"[tool]Calling tool: {tool_name}[/]")
                            console.print(
                                f"[tool]Input: {json.dumps(make_json_serializable(tool_input), indent=2)}[/]"
                            )

                            # Add tool use to follow-up messages
                            follow_up_messages.append(
                                {
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "tool_use",
                                            "name": tool_name,
                                            "id": tool_id,
                                            "input": make_json_serializable(tool_input),
                                        }
                                    ],
                                }
                            )

                            try:
                                # Execute the tool - FastMCP's Client handles serialization
                                result = await client.call_tool(tool_name, tool_input)

                                # Log the result
                                console.print(
                                    f"[tool]Result: {json.dumps(make_json_serializable(result), indent=2)}[/]"
                                )

                                # Add tool result to follow-up messages
                                follow_up_messages.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_id,
                                                "content": json.dumps(
                                                    make_json_serializable(result), indent=2
                                                ),
                                            }
                                        ],
                                    }
                                )

                            except Exception as e:
                                error_message = f"Error executing tool: {str(e)}"
                                console.print(f"[error]{error_message}[/]")

                                # Add error message to follow-up messages
                                follow_up_messages.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_id,
                                                "content": error_message,
                                            }
                                        ],
                                    }
                                )

                    # If there were tool calls, get Claude's final response
                    if need_follow_up:
                        start_spinner("Processing results")

                        final_response = await anthropic.messages.create(
                            model=MODEL,
                            max_tokens=4096,
                            system=system_message,
                            messages=follow_up_messages,
                        )

                        stop_spinner()

                        # Process the final response
                        for content_block in final_response.content:
                            if content_block.type == "text":
                                console.print(
                                    Panel(
                                        f"[assistant]{content_block.text}[/]", border_style="green"
                                    )
                                )

                                # Add to message history
                                messages.append(
                                    {"role": "assistant", "content": content_block.text}
                                )

                except Exception as e:
                    # Stop spinner if there was an error
                    stop_spinner()
                    console.print(f"[error]Error: {str(e)}[/]")

    except Exception as e:
        console.print(f"[error]Failed to connect to MCP server: {str(e)}[/]")
        console.print(f"[system]Please make sure the server file exists at todo_mcp/server.py[/]")

    finally:
        # Make sure spinner is stopped
        stop_spinner()
        console.print("[system]Todo Chat CLI ended.[/]")


@app.command()
def main():
    """Run the Todo Chat CLI."""
    try:
        asyncio.run(chat_loop())
    except Exception as e:
        console.print(f"[error]Unhandled error: {str(e)}[/]")
        exit(1)


if __name__ == "__main__":
    app()

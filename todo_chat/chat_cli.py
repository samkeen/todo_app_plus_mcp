"""
Todo Chat CLI

A simple command-line chat interface that connects to Claude and allows
interaction with the Todo app via the MCP server.

Usage:
    python -m todo_chat.chat_cli

Requirements:
    - An Anthropic API key (set as ANTHROPIC_API_KEY environment variable)
    - The Todo MCP server running locally
"""

import os
import sys
import json
import asyncio
import time
from typing import List, Dict, Any, Optional, Union, TypedDict, cast, Tuple, Iterable
from threading import Thread
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from anthropic import AsyncAnthropic
from anthropic.types import (
    MessageParam, 
    ToolParam, 
    ContentBlockParam,
    TextBlockParam,
    ToolUseBlockParam,
    ToolResultBlockParam
)

# Load environment variables from .env file if it exists
load_dotenv()

# Check for API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY environment variable not found.")
    print("Please set your Anthropic API key in the .env file or as an environment variable.")
    sys.exit(1)

# Configuration
MODEL = "claude-3-opus-20240229"  # You can change this to any Claude model
MAX_TOKENS = 4096

# ANSI color codes for terminal output
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "user": "\033[1;34m",  # Blue for user
    "assistant": "\033[1;32m",  # Green for assistant
    "system": "\033[1;33m",  # Yellow for system messages
    "error": "\033[1;31m",  # Red for errors
    "tool": "\033[1;36m",  # Cyan for tool calls
    "spinner": "\033[1;35m",  # Magenta for spinner (more contrasting)
    "spinner_text": "\033[1;37m",  # Bright white for spinner text
}

# TypedDict for our session structure
class MCPSessionData(TypedDict):
    session: ClientSession
    client: Any

# Define TypedDict for tool definitions
class ClaudeToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: Dict[str, Any]

# Initialize Anthropic client
anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# Global variables
mcp_session: Optional[MCPSessionData] = None
tool_definitions: List[ClaudeToolDefinition] = []
messages: List[MessageParam] = []
spinner_running = False
spinner_thread: Optional[Thread] = None

def start_spinner(message: str = "Thinking") -> None:
    """Start a spinner animation in the terminal."""
    global spinner_running, spinner_thread
    
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    
    def spin() -> None:
        nonlocal i
        while spinner_running:
            # Clear the current line and print spinner with message
            sys.stdout.write(f"\r{COLORS['spinner']}{spinner_frames[i]}{COLORS['reset']} {COLORS['spinner_text']}{message}...{COLORS['reset']}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(spinner_frames)
    
    spinner_running = True
    spinner_thread = Thread(target=spin)
    spinner_thread.daemon = True
    spinner_thread.start()

def stop_spinner() -> None:
    """Stop the spinner animation and clear the line."""
    global spinner_running, spinner_thread
    
    if spinner_running and spinner_thread:
        spinner_running = False
        spinner_thread.join(timeout=0.5)  # Wait for spinner thread to finish
        # Clear spinner line
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()
        spinner_thread = None

async def setup_mcp() -> bool:
    """Set up MCP session and discover tools."""
    global mcp_session, tool_definitions

    print(f"{COLORS['system']}Connecting to MCP server...{COLORS['reset']}")

    try:
        # Set up MCP server connection
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "todo_mcp.server"],
        )

        # Use proper async with for context managers
        client_ctx = stdio_client(server_params)
        read, write = await client_ctx.__aenter__()
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        
        # Store both context managers for proper cleanup
        mcp_session = {
            "session": session,
            "client": client_ctx,
        }

        # Discover tools
        print(f"{COLORS['system']}Discovering tools...{COLORS['reset']}")
        if mcp_session is not None:
            mcp_tools = await mcp_session["session"].list_tools()
            
            # Convert tools to list for easier handling
            tools_list = list(mcp_tools) if hasattr(mcp_tools, "__iter__") else []
            
            # Print raw tools for debugging
            print(f"{COLORS['system']}Found {len(tools_list)} raw tools from MCP server{COLORS['reset']}")
            
            # Extract the actual tools which are nested in the 'tools' field
            actual_tools = []
            for item in tools_list:
                # Handle object-style attributes (hasattr check first)
                if hasattr(item, "name") and hasattr(item, "description"):
                    if getattr(item, "name") == "tools":
                        description_value = getattr(item, "description")
                        if isinstance(description_value, list):
                            actual_tools.extend(description_value)
                            print(f"{COLORS['system']}Extracted {len(actual_tools)} actual tools from 'tools' field{COLORS['reset']}")
                # Handle tuple-style attributes
                elif isinstance(item, tuple) and len(item) >= 2:
                    if item[0] == "tools" and isinstance(item[1], list):
                        actual_tools.extend(item[1])
                        print(f"{COLORS['system']}Extracted {len(actual_tools)} actual tools from 'tools' tuple{COLORS['reset']}")
            
            # If no tools were found in the nested structure, fall back to the original list
            if not actual_tools:
                actual_tools = tools_list
            
            # Print all the actual tools
            for i, tool in enumerate(actual_tools):
                print(f"{COLORS['system']}Tool {i+1}:{COLORS['reset']}")
                if hasattr(tool, "name") and hasattr(tool, "description"):
                    print(f"{COLORS['system']}  - Name: {getattr(tool, 'name')}{COLORS['reset']}")
                    print(f"{COLORS['system']}  - Description: {str(getattr(tool, 'description'))[:100]}...{COLORS['reset']}")
                elif isinstance(tool, tuple) and len(tool) >= 2:
                    print(f"{COLORS['system']}  - Name: {tool[0]}{COLORS['reset']}")
                    print(f"{COLORS['system']}  - Description: {str(tool[1])[:100]}...{COLORS['reset']}")
                else:
                    print(f"{COLORS['system']}  - Unknown format: {type(tool)}{COLORS['reset']}")

            # Also list any prompts
            try:
                prompts = await mcp_session["session"].list_prompts()
                prompts_list = list(prompts) if hasattr(prompts, "__iter__") else []
                print(f"{COLORS['system']}Found {len(prompts_list)} prompts from MCP server{COLORS['reset']}")
                
                # Extract the actual prompts which are nested in the 'prompts' field
                actual_prompts = []
                for item in prompts_list:
                    # Handle object-style attributes (hasattr check first)
                    if hasattr(item, "name") and hasattr(item, "description"):
                        if getattr(item, "name") == "prompts":
                            description_value = getattr(item, "description")
                            if isinstance(description_value, list):
                                actual_prompts.extend(description_value)
                                print(f"{COLORS['system']}Extracted {len(actual_prompts)} actual prompts from 'prompts' field{COLORS['reset']}")
                    # Handle tuple-style attributes
                    elif isinstance(item, tuple) and len(item) >= 2:
                        if item[0] == "prompts" and isinstance(item[1], list):
                            actual_prompts.extend(item[1])
                            print(f"{COLORS['system']}Extracted {len(actual_prompts)} actual prompts from 'prompts' tuple{COLORS['reset']}")
                
                # If no prompts were found in the nested structure, fall back to the original list
                if not actual_prompts:
                    actual_prompts = prompts_list
                
                # Print all the actual prompts
                for i, prompt in enumerate(actual_prompts):
                    print(f"{COLORS['system']}Prompt {i+1}:{COLORS['reset']}")
                    if hasattr(prompt, "name") and hasattr(prompt, "description"):
                        print(f"{COLORS['system']}  - Name: {getattr(prompt, 'name')}{COLORS['reset']}")
                        print(f"{COLORS['system']}  - Description: {str(getattr(prompt, 'description'))[:100]}...{COLORS['reset']}")
                    elif isinstance(prompt, tuple) and len(prompt) >= 2:
                        print(f"{COLORS['system']}  - Name: {prompt[0]}{COLORS['reset']}")
                        print(f"{COLORS['system']}  - Description: {str(prompt[1])[:100]}...{COLORS['reset']}")
                    else:
                        print(f"{COLORS['system']}  - Unknown format: {type(prompt)}{COLORS['reset']}")
            except Exception as e:
                print(f"{COLORS['error']}Error listing prompts: {str(e)}{COLORS['reset']}")

            # Convert to Anthropic tool format
            for tool in actual_tools:
                # Extract the tool's name, description, and parameter schema
                tool_name = ""
                tool_description = ""
                tool_schema: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}
                
                # Handle different tool formats based on MCP version
                if hasattr(tool, "name") and hasattr(tool, "description"):
                    tool_name = str(getattr(tool, "name"))
                    tool_description = str(getattr(tool, "description"))
                    if hasattr(tool, "inputSchema"):
                        tool_schema = getattr(tool, "inputSchema")
                    elif hasattr(tool, "parameter_schema"):
                        tool_schema = getattr(tool, "parameter_schema")
                elif isinstance(tool, tuple) and len(tool) >= 2:
                    tool_name = str(tool[0])
                    tool_description = str(tool[1])
                    if len(tool) >= 3 and isinstance(tool[2], dict):
                        tool_schema = tool[2]
                else:
                    continue

                # Add tool definition
                tool_def: ClaudeToolDefinition = {
                    "name": tool_name,
                    "description": tool_description,
                    "input_schema": tool_schema
                }
                tool_definitions.append(tool_def)

            print(f"{COLORS['system']}Converted {len(tool_definitions)} tools to Claude format{COLORS['reset']}")
            for i, tool in enumerate(tool_definitions):
                print(f"{COLORS['system']}Converted Tool {i+1}: {tool['name']} - {tool['description'][:50]}...{COLORS['reset']}")
            
            return True
        return False

    except Exception as e:
        print(f"{COLORS['error']}Failed to connect to MCP server: {str(e)}{COLORS['reset']}")
        print(
            f"{COLORS['system']}Please start the MCP server with: python -m todo_mcp.server{COLORS['reset']}"
        )
        return False


async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool."""
    global mcp_session

    print(f"{COLORS['tool']}Executing tool: {tool_name}{COLORS['reset']}")
    print(f"{COLORS['tool']}Parameters: {json.dumps(tool_input, indent=2)}{COLORS['reset']}")

    try:
        if mcp_session is not None:
            raw_result = await mcp_session["session"].call_tool(tool_name, tool_input)
            
            # Convert the result to a serializable format
            result_dict = make_json_serializable(raw_result)
            
            # Print the result for debugging
            try:
                print(f"{COLORS['tool']}Result: {json.dumps(result_dict, indent=2)}{COLORS['reset']}")
            except TypeError as e:
                print(f"{COLORS['error']}Result still not JSON serializable: {str(e)}{COLORS['reset']}")
                print(f"{COLORS['tool']}Raw Result: {str(result_dict)}{COLORS['reset']}")
                
                # Final fallback: Convert to a simple string representation
                result_dict = {"result": str(result_dict)}
                
            return result_dict
    except Exception as e:
        print(f"{COLORS['error']}Tool execution failed: {str(e)}{COLORS['reset']}")
    
    return {"error": "Tool execution failed"}


def make_json_serializable(obj: Any) -> Any:
    """Recursively convert an object to a JSON serializable format."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        # Basic types are already serializable
        return obj
    
    elif isinstance(obj, dict):
        # Process each value in the dictionary
        return {k: make_json_serializable(v) for k, v in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        # Process each item in the list/tuple
        return [make_json_serializable(item) for item in obj]
    
    elif hasattr(obj, "content") and isinstance(obj.content, list):
        # Special handling for objects with a content field containing a list
        result = {"content": []}
        
        # Process each content item
        for item in obj.content:
            if hasattr(item, "text"):
                # If the item has text, extract it
                try:
                    # Try to parse the text as JSON
                    text_value = item.text
                    try:
                        json_obj = json.loads(text_value)
                        result["content"].append(json_obj)
                    except json.JSONDecodeError:
                        # If not valid JSON, use as string
                        result["content"].append(text_value)
                except Exception:
                    # Fallback to string representation
                    result["content"].append(str(item))
            else:
                # Fallback for other types
                result["content"].append(make_json_serializable(item))
        
        # Add any other attributes
        for attr_name in dir(obj):
            if not attr_name.startswith("_") and attr_name != "content":
                try:
                    attr_value = getattr(obj, attr_name)
                    if not callable(attr_value):
                        result[attr_name] = make_json_serializable(attr_value)
                except Exception:
                    pass
        
        return result
    
    elif hasattr(obj, "__dict__"):
        # For objects with a __dict__, convert it recursively
        return make_json_serializable(obj.__dict__)
    
    elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        # For objects with a to_dict method, use it
        try:
            return make_json_serializable(obj.to_dict())
        except Exception:
            pass
    
    # Final fallback: convert to string
    return str(obj)


async def chat_loop() -> None:
    """Main chat loop."""
    global messages, mcp_session

    print(f"{COLORS['system']}Starting Todo Chat CLI...{COLORS['reset']}")
    print(f"{COLORS['system']}Type 'exit' or 'quit' to end the conversation.{COLORS['reset']}")

    # Setup MCP
    if not await setup_mcp():
        return

    # Store system message separately since Claude API expects it as a top-level parameter
    system_message = """You are Todo Assistant, an AI that helps users manage their todo list through natural language.
Your primary function is to create and manage todo items by intelligently converting user statements into todo items.

Key behaviors:
1. When a user mentions a task or action they need to do, ALWAYS assume they want to create a todo item for it.
2. Interpret statements like "call mom tomorrow" as a request to create a todo with that title.
3. Extract relevant details from user input to create todo items with descriptive titles and useful descriptions.
4. ALWAYS use the provided tools to interact with the todo list.
5. Be helpful, friendly, and concise in your responses.
6. Focus on confirming the task was added and providing the essential details.

Your available tools allow you to:
- Create new todo items
- Update existing todo items
- List all todo items
- Delete todo items
- Get a specific todo item by ID
- View statistics about the todo list

For any user input that might reasonably be interpreted as a task, convert it to a todo item without asking for confirmation first.
"""
    # Initialize messages as an empty list (system message will be passed separately)
    messages = []

    # Welcome message
    print(
        f"{COLORS['assistant']}Todo Assistant: Hello! I'm your Todo Assistant. I can help you manage your todo list through natural language. What would you like to do with your todos today?{COLORS['reset']}"
    )

    try:
        while True:
            # Get user input
            user_input = input(f"{COLORS['user']}You: {COLORS['reset']}")

            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(
                    f"{COLORS['assistant']}Todo Assistant: Goodbye! Have a great day!{COLORS['reset']}"
                )
                break

            # Add user message to history
            user_message: MessageParam = {"role": "user", "content": user_input}
            messages.append(user_message)

            # Start spinner while waiting for Claude's response
            start_spinner("Generating response")
            
            try:
                # Create a message with Claude
                response = await anthropic_client.messages.create(
                    model=MODEL, 
                    max_tokens=MAX_TOKENS,
                    system=system_message,  # Pass system message as a separate parameter
                    messages=messages, 
                    tools=cast(List[ToolParam], tool_definitions)
                )
                
                # Stop spinner after receiving response
                stop_spinner()

                # Process the response
                has_tool_calls = False

                for content_block in response.content:
                    if content_block.type == "text":
                        # Regular text response
                        print(f"{COLORS['assistant']}Claude: {content_block.text}{COLORS['reset']}")
                        assistant_message: MessageParam = {"role": "assistant", "content": content_block.text}
                        messages.append(assistant_message)

                    elif content_block.type == "tool_use":
                        # Tool call
                        has_tool_calls = True
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_id = content_block.id

                        # Create a proper ToolUseBlockParam
                        tool_use_block: ToolUseBlockParam = {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_input
                        }
                        
                        # Add tool call to message history using properly typed content blocks
                        tool_message: MessageParam = {
                            "role": "assistant",
                            "content": [tool_use_block]
                        }
                        messages.append(tool_message)

                        # Execute the tool
                        result = await execute_tool(tool_name, cast(Dict[str, Any], tool_input))

                        # Create a proper ToolResultBlockParam
                        tool_result_block: ToolResultBlockParam = {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        }
                        
                        # Add tool result to message history
                        result_message: MessageParam = {
                            "role": "user",
                            "content": [tool_result_block]
                        }
                        messages.append(result_message)

                # If there were tool calls, get Claude's final response
                if has_tool_calls:
                    # Start spinner again while waiting for Claude's final response
                    start_spinner("Processing results")
                    
                    final_response = await anthropic_client.messages.create(
                        model=MODEL, 
                        max_tokens=MAX_TOKENS,
                        system=system_message,  # Pass system message as a separate parameter
                        messages=messages
                    )
                    
                    # Stop spinner after receiving final response
                    stop_spinner()

                    # Process the final response (should only contain text)
                    for content_block in final_response.content:
                        if content_block.type == "text":
                            print(f"{COLORS['assistant']}Claude: {content_block.text}{COLORS['reset']}")
                            # Create a text response
                            final_text: TextBlockParam = {
                                "type": "text",
                                "text": content_block.text
                            }
                            final_message: MessageParam = {
                                "role": "assistant", 
                                "content": [final_text]
                            }
                            messages.append(final_message)
            except Exception as e:
                # Stop spinner if there was an error
                stop_spinner()
                print(f"{COLORS['error']}Error: {str(e)}{COLORS['reset']}")

    except KeyboardInterrupt:
        # Stop spinner if KeyboardInterrupt
        stop_spinner()
        print(f"\n{COLORS['system']}Chat session ended by user.{COLORS['reset']}")

    except Exception as e:
        # Stop spinner if there was an error
        stop_spinner()
        print(f"{COLORS['error']}Error: {str(e)}{COLORS['reset']}")

    finally:
        # Make sure to stop spinner if it's still running
        if spinner_running:
            stop_spinner()
            
        # Clean up: Close the MCP session
        if mcp_session is not None:
            try:
                # Close session first, then client
                await mcp_session["session"].__aexit__(None, None, None)
                await mcp_session["client"].__aexit__(None, None, None)
                print(f"{COLORS['system']}MCP session closed.{COLORS['reset']}")
            except Exception as e:
                print(f"{COLORS['error']}Error closing MCP session: {str(e)}{COLORS['reset']}")

        print(f"{COLORS['system']}Todo Chat CLI ended.{COLORS['reset']}")


if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except Exception as e:
        print(f"{COLORS['error']}Unhandled error: {str(e)}{COLORS['reset']}")
        sys.exit(1)

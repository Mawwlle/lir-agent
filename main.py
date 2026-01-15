import sys
import os
import logging
import asyncio
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
import subprocess
import importlib.util
from pathlib import Path
from typing import Any, Callable
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from langchain_core.messages import AIMessage


logging.basicConfig(
    level=logging.INFO,
    format='\033[36m%(asctime)s\033[0m | \033[32m%(levelname)s\033[0m | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

TOOLS: dict[str, Callable[..., Any]] = {}

TOOL_DIR = Path("./runtime_tools")
TOOL_DIR.mkdir(exist_ok=True)
(TOOL_DIR / '__init__.py').touch(exist_ok=True)

@tool
def install_dependency(
    dependency: str,
    version: str | None = None,
    **kwargs,
) -> str:
    """Install a Python package ONLY inside a virtual environment."""

    if sys.prefix == sys.base_prefix:
        return "Error: not running inside a virtual environment."

    if importlib.util.find_spec("pip") is None:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "ensurepip", "--upgrade"]
            )
        except subprocess.CalledProcessError:
            return "Error: pip is not available."

    if importlib.util.find_spec(dependency) is not None:
        return f"{dependency} already installed."

    pkg = f"{dependency}=={version}" if version else dependency

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return f"Installed {pkg}"
    except subprocess.CalledProcessError as e:
        return f"Installation failed: {e}"

@tool
def create_tool(
    tool_name: str,
    code: str,
    entrypoint: str,
    description: str,
    **kwargs,
) -> str:
    """
    Create a Python tool as a module, import it, and register it.
    """

    logger.info(f"Creating runtime tool: {tool_name}")
    
    file_path = TOOL_DIR / f"{tool_name}.py"
    file_path.write_text(code)

    spec = importlib.util.spec_from_file_location(tool_name, file_path)
    
    if not spec or not spec.loader:
        error_msg = f"Tool {tool_name} cannot get spec by file location. Tool not created!"
        logger.error(error_msg)
        return error_msg

    module = importlib.util.module_from_spec(spec)
    sys.modules[tool_name] = module
    spec.loader.exec_module(module) 

    fn = getattr(module, entrypoint)

    TOOLS[tool_name] = fn
    
    success_msg = (
        f"Tool '{tool_name}' registered. "
        f"Entrypoint: '{entrypoint}'. "
        f"Description: {description}"
    )
    logger.info(f"Success: {success_msg}")

    return success_msg

@tool
def dynamic_tool(tool_name: str, **kwargs) -> Any:
    """
        Dynamically call a tool.
        - If args is a dict → pass as **args
        - If args is a list or tuple → pass as *args
    """
    if tool_name not in TOOLS:
        error_msg = f"Error: unknown tool '{tool_name}'. Available tools: {list(TOOLS.keys())}"
        logger.warning(error_msg)
        return error_msg

    fn = TOOLS[tool_name]
    logger.info(f"Executing tool: {tool_name}")
    
    if 'kwargs' in kwargs:
        kwargs = kwargs['kwargs']
    
    try:
        # Handle StructuredTool objects (from @tool decorator)
        if isinstance(fn, StructuredTool):
            # Extract the underlying function from StructuredTool
            underlying_func = fn.func
            if underlying_func:
                result = underlying_func(**kwargs)
            else:
                error_msg = f"Error: underlying function not found for tool '{tool_name}'"
                logger.error(error_msg)
                return error_msg
        else:
            # Regular function call
            result = fn(**kwargs)
        return result
    except Exception as err:
        error_msg = f'Failed to call this tool. Reason: {err}'
        logger.error(f"Error: {error_msg}")
        return error_msg

@tool
def list_tools(**kwargs) -> list[str]:
    """List available tools."""
    return list(TOOLS.keys())



load_dotenv(find_dotenv(usecwd=True))

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

if not API_KEY:
    raise ValueError("API_KEY environment variable is required")
if not MODEL_NAME:
    raise ValueError("MODEL_NAME environment variable is required")

custom_headers = {}
headers_env = os.getenv("CUSTOM_HEADERS", "")
if headers_env:
    for header_pair in headers_env.split(","):
        if ":" in header_pair:
            key, value = header_pair.split(":", 1)
            custom_headers[key.strip()] = value.strip()

default_headers = {
    "User-Agent": "lir-agent/0.1.0",
    **custom_headers
}

llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,  # type: ignore
    model=MODEL_NAME,
    temperature=0.7,
    default_headers=default_headers,
)

ACTOR_PROMPT = """
    You are a tool-creating agent. Your PRIMARY goal is to CREATE and USE runtime tools to solve problems.
    
    CRITICAL RULES:
    1. NEVER give direct answers or explanations unless the task is purely informational
    2. ALWAYS prioritize creating a tool if one doesn't exist for the task
    3. ALWAYS use tools to execute actions, not direct responses
    4. If a tool might help, CREATE IT FIRST, then USE IT
    
    You follow a ReAct loop:
    Thought → Action → Observation → Thought → Action → ...
    
    WORKFLOW:
    1. First, check available tools: use list_tools
    2. If no suitable tool exists: CREATE ONE using create_tool
    3. If tool exists: USE IT via dynamic_tool
    4. If dependencies needed: use install_dependency first
    
    When creating a tool:
    - Think: "I need to [task]. Let me create a tool for this."
    - Action: create_tool with proper Python code
    - Observation: tool registered
    - Action: dynamic_tool to execute the new tool
    
    Tool creation template:
    ```python
    from langchain.tools import tool

    @tool
    def tool_name(*, param1: str, param2: str, **kwargs) -> str:
        \"\"\"Clear description of what the tool does.\"\"\"
        # Implementation here
        return result
    ```
    
    Available actions:
    - list_tools: Check what tools are available
    - create_tool: Create a new runtime tool (tool_name, code, entrypoint, description)
    - dynamic_tool: Execute a tool (tool_name, **kwargs)
    - install_dependency: Install Python packages (dependency, version)
    
    REMEMBER: Create tools first, use tools always. Direct responses are last resort.
"""

actor_agent = create_agent(
    model=llm,
    tools=[
        dynamic_tool,
        list_tools,
        create_tool,
        install_dependency,
    ],
    system_prompt=ACTOR_PROMPT,
)


async def _stream_agent_thoughts_async(agent, user_input: str) -> AIMessage:
    print("\n\033[1mThinking...\033[0m\n")
    
    messages = [{"role": "user", "content": user_input}]
    final_result = None
    streamed_content = []
    
    try:
        # Stream events to capture thoughts
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2"
        ):
            event_kind = event.get("event")
            
            # Stream model thoughts/content
            if event_kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        print(content, end="", flush=True)
                        streamed_content.append(content)
            
            # Capture final result
            elif event_kind == "on_chain_end":
                name = event.get("name", "")
                if "agent" in name.lower() or name == "":
                    output = event.get("data", {}).get("output")
                    if output:
                        final_result = output
        
        # Fallback: if streaming didn't work, use regular invoke
        if final_result is None:
            logger.warning("Streaming incomplete, using standard invoke")
            final_result = agent.invoke({"messages": messages})
            
    except Exception as e:
        logger.error(f"Streaming error: {e}, falling back to invoke")
        final_result = agent.invoke({"messages": messages})
    
    print("\n")
    

    if isinstance(final_result, dict):
        messages_list = final_result.get("messages", [])
        for msg in messages_list:
            if isinstance(msg, AIMessage):
                return msg

        content = str(final_result.get("output", final_result))
        return AIMessage(content=content)
    elif isinstance(final_result, AIMessage):
        return final_result
    else:
        return AIMessage(content=str(final_result))


def stream_agent_thoughts(agent, user_input: str) -> AIMessage:
    return asyncio.run(_stream_agent_thoughts_async(agent, user_input))


def chat_cli():
    print("\n" + "="*60)
    print("\033[1m\033[36m  LIR Agent - CLI Chat\033[0m")
    print("="*60)
    print("\033[90mType 'exit' or 'quit' to end the conversation\033[0m\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\033[1mYou:\033[0m ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n\033[36mGoodbye!\033[0m\n")
                break
            
            # Stream agent response and get AIMessage
            result = stream_agent_thoughts(actor_agent, user_input)
            
        except KeyboardInterrupt:
            print("\n\n\033[36mInterrupted. Goodbye!\033[0m\n")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n\033[31mError: {e}\033[0m\n")


if __name__ == "__main__":
    chat_cli()
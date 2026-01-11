import sys

import os
from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
import subprocess
import importlib.util
from pathlib import Path
from typing import Any, Callable
from langchain.agents import create_agent
from langchain.tools import tool
import json

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

    file_path = TOOL_DIR / f"{tool_name}.py"
    file_path.write_text(code)

    spec = importlib.util.spec_from_file_location(tool_name, file_path)
    
    if not spec or not spec.loader:
        return f"Tool {tool_name} cannot get spec by file location. Tool not created!"

    module = importlib.util.module_from_spec(spec)
    sys.modules[tool_name] = module
    spec.loader.exec_module(module) 

    fn = getattr(module, entrypoint)

    TOOLS[tool_name] = fn

    return (
        f"Tool '{tool_name}' registered. "
        f"Entrypoint: '{entrypoint}'. "
        f"Description: {description}"
    )

@tool
def dynamic_tool(tool_name: str, **kwargs) -> Any:
    """
    Dynamically call a tool.
    - If args is a dict → pass as **args
    - If args is a list or tuple → pass as *args
    """
    if tool_name not in TOOLS:
        return f"Error: unknown tool '{tool_name}'"

    fn = TOOLS[tool_name]
    
    if 'kwargs' in kwargs:
        kwargs = kwargs['kwargs']
    
    try:
        return fn(**kwargs)
    except Exception as err:
        return f'Failed to call this tool. Reason: {err}'

@tool
def list_tools(**kwargs) -> list[str]:
    """List available tools."""
    return list(TOOLS.keys())



load_dotenv(find_dotenv(usecwd=True))

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    model=MODEL_NAME,
    temperature=0.7,
)

ACTOR_PROMPT = """
    You follow a ReAct loop:

    Thought → Action → Observation

    If you need a tool that does not exist:
    - Think: "ToolMissing"
    - Action: create_tool
    - Observation: tool registered

    Write tool creation code as a Python function with proper signature:
    ```python
    from langchain.tools import tool

    @tool
    def hello_world(*, some_val: str, some_val_2: str, **kwargs) -> str:
        return f'{some_val}/{some_val_2}'
    ```



    Available actions:
    - dynamic_tool Call tools only with keyword arguments like - `dynamic_tool(some_val='abiba', some_val_2='abiba', tool_name='hello')`
    - list_tools
    - create_tool
    - install_dependency
    DYNAMIC ACTIONS CAN CHECK IN list_tools
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

user_input = 'Start simple fastapi server on port 4555. Call tool for start is start_web and execute it'
result = actor_agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })


print(result)
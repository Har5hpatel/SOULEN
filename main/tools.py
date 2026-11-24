"""SOULEN tool registry (Step 1B)."""
from datetime import datetime

TOOLS: dict[str, dict] = {}


def tool(description: str):
    """Decorator that registers a function as a tool."""
    def decorator(func):
        TOOLS[func.__name__] = {"func": func, "description": description}
        return func
    return decorator


def run_tool(name: str, args: dict | None = None) -> str:
    """Run a registered tool by name. Never crashes, always returns text."""
    if name not in TOOLS:
        return f"Error: unknown tool '{name}'"
    try:
        return str(TOOLS[name]["func"](**(args or {})))
    except Exception as e:
        return f"Error running {name}: {e}"


@tool("Get the current local time")
def get_current_time() -> str:
    return datetime.now().strftime("%I:%M %p")


@tool("Get today's date")
def get_current_date() -> str:
    return datetime.now().strftime("%A, %d %B %Y")

import os
import importlib
import inspect
import functools
import pkgutil
import sys

from mcp.server.fastmcp import FastMCP
from secops.chronicle.client import ChronicleClient

# Initialize Chronicle Client
project_id = os.environ.get("PROJECT_ID")
customer_id = os.environ.get("CUSTOMER_ID")
region = os.environ.get("CHRONICLE_REGION", "us")

# Initialize FastMCP
mcp = FastMCP("SecOps")

# Global client instance
_client = None

def get_client():
    global _client
    if _client is None:
        if not project_id or not customer_id:
            # If not set, we can't really function as a tool that requires auth
            # But maybe we can rely on default credentials if we construct Client differently?
            # ChronicleClient seems to require them.
            # We raise error only when the tool is called.
            pass

        if project_id and customer_id:
            _client = ChronicleClient(project_id=project_id, customer_id=customer_id, region=region)

    if _client is None:
         raise ValueError("PROJECT_ID and CUSTOMER_ID environment variables must be set.")

    return _client

def discover_tools():
    """Dynamically discover tools in secops.chronicle package"""
    tools = []
    import secops.chronicle

    for module_info in pkgutil.iter_modules(secops.chronicle.__path__):
        if module_info.name == "client":
            continue

        module_name = f"secops.chronicle.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            # print(f"Skipping {module_name} due to import error: {e}")
            continue

        for name, obj in inspect.getmembers(module):
            if not inspect.isfunction(obj):
                continue

            if name.startswith("_"):
                continue

            if obj.__module__ != module_name:
                continue

            try:
                sig = inspect.signature(obj)
                params = list(sig.parameters.values())

                if not params:
                    continue

                # Check if first argument is likely 'client'
                first_param = params[0]
                if first_param.name == "client":
                    tools.append((module_name, name, obj))
            except ValueError:
                continue
    return tools

def register_tools():
    tools = discover_tools()
    for module_name, func_name, func in tools:
        try:
            # Wrapper to inject client
            # We need to preserve signature but remove 'client'

            sig = inspect.signature(func)
            params = list(sig.parameters.values())

            # Remove 'client' (first argument)
            new_params = params[1:]
            new_sig = sig.replace(parameters=new_params)

            # Create wrapper with captured func
            def create_wrapper(f):
                @functools.wraps(f)
                def wrapper(*args, **kwargs):
                    client = get_client()
                    return f(client, *args, **kwargs)
                return wrapper

            wrapper = create_wrapper(func)

            wrapper.__signature__ = new_sig

            mcp.add_tool(wrapper)

            # Expose the wrapper in this module's namespace
            # This allows "from secops.mcp_server import get_alerts"
            setattr(sys.modules[__name__], func_name, wrapper)

        except Exception as e:
            print(f"Error registering {func_name}: {e}")

# Register tools on import
register_tools()

def start():
    """Entry point to start the MCP server"""
    mcp.run()

if __name__ == "__main__":
    import sys
    # Hack to make sure mcp.run() sees command line args
    start()

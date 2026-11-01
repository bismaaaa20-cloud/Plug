"""Built-in Plug plugin. Implementation lives in plug.builtin_catalog."""
from plug.builtin_catalog import run_builtin

def run(context, arguments):
    return run_builtin(context, arguments)

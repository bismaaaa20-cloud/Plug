"""Plug first-party plugin entrypoint."""
from plug.builtin_catalog import run_builtin

def run(context, arguments):
    return run_builtin(context, arguments)

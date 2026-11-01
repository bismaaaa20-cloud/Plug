"""Metadata entrypoint for python-testing."""
SKILL_NAME = "python-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

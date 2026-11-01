"""Metadata entrypoint for web-content-operations."""
SKILL_NAME = "web-content-operations"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

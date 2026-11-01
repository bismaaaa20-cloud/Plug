"""Metadata entrypoint for performance-budgeting."""
SKILL_NAME = "performance-budgeting"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

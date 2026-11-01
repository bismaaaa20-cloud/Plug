"""Metadata entrypoint for operations-analytics."""
SKILL_NAME = "operations-analytics"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Metadata entrypoint for procurement-planning."""
SKILL_NAME = "procurement-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

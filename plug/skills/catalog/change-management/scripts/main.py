"""Metadata entrypoint for change-management."""
SKILL_NAME = "change-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

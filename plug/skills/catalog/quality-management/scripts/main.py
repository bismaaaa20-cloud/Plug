"""Metadata entrypoint for quality-management."""
SKILL_NAME = "quality-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

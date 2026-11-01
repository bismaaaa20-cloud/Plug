"""Metadata entrypoint for community-management."""
SKILL_NAME = "community-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

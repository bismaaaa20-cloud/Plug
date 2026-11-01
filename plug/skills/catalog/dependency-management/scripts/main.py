"""Metadata entrypoint for dependency-management."""
SKILL_NAME = "dependency-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

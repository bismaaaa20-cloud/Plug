"""Metadata entrypoint for knowledge-management."""
SKILL_NAME = "knowledge-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

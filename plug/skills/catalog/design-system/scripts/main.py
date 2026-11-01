"""Metadata entrypoint for design-system."""
SKILL_NAME = "design-system"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

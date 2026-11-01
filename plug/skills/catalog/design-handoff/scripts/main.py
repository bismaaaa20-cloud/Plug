"""Metadata entrypoint for design-handoff."""
SKILL_NAME = "design-handoff"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Metadata entrypoint for component-library."""
SKILL_NAME = "component-library"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

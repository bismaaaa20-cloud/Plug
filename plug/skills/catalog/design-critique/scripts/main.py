"""Metadata entrypoint for design-critique."""
SKILL_NAME = "design-critique"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Helper entrypoint for the brand-naming skill."""

SKILL_NAME = "brand-naming"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Helper entrypoint for the debugging skill."""

SKILL_NAME = "debugging"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

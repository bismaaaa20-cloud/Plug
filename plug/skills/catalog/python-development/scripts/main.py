"""Helper entrypoint for the python-development skill."""

SKILL_NAME = "python-development"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

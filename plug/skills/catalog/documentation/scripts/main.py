"""Helper entrypoint for the documentation skill."""

SKILL_NAME = "documentation"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

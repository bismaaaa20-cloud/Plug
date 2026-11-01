"""Helper entrypoint for the logo-brief skill."""

SKILL_NAME = "logo-brief"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

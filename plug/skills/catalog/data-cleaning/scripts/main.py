"""Helper entrypoint for the data-cleaning skill."""

SKILL_NAME = "data-cleaning"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

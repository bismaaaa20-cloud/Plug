"""Helper entrypoint for the learning-coach skill."""

SKILL_NAME = "learning-coach"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

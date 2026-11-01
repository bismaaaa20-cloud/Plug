"""Helper entrypoint for the translation skill."""

SKILL_NAME = "translation"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

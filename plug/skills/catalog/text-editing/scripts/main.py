"""Helper entrypoint for the text-editing skill."""

SKILL_NAME = "text-editing"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
